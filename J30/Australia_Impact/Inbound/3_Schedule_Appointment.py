import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env
from Australia_Impact.Inbound.Inbound_payload_generation.Appointment_Payload import (
    Appointment_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Schedule_Appointment:
    @staticmethod
    def _extract_appointment_ids(response_data: object) -> list[str]:
        appointment_ids = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    normalized_key = key.replace("_", "").lower()
                    if normalized_key.endswith("appointmentid") and value not in (None, ""):
                        appointment_ids.append(str(value))
                    if normalized_key == "description" and isinstance(value, str):
                        apt_matches = re.findall(r"Apt-\d+", value)
                        appointment_ids.extend(apt_matches)
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(response_data)

        deduped = []
        seen = set()
        for appt_id in appointment_ids:
            if appt_id in seen:
                continue
            seen.add(appt_id)
            deduped.append(appt_id)
        return deduped

    @staticmethod
    def _normalize_shipment_list(raw_value: str) -> list[str]:
        seen = set()
        normalized = []
        for shipment_id in str(raw_value).split(";"):
            shipment_id = shipment_id.strip()
            if not shipment_id or shipment_id in seen:
                continue
            seen.add(shipment_id)
            normalized.append(shipment_id)
        return normalized

    def _update_master_input_appt_id(self, updates: list[dict]):
        if not updates:
            return

        worksheet = Worksheet()
        workbook_path = Path(worksheet.master_file_path)
        try:
            master_df = pd.read_excel(workbook_path, sheet_name="MasterInput", dtype=str).fillna("")
        except Exception as ex:
            logging.error(f"Failed to read MasterInput from {workbook_path}: {ex}")
            return

        if "Appt_id" not in master_df.columns:
            master_df["Appt_id"] = ""
        if "TrailerId" not in master_df.columns:
            master_df["TrailerId"] = ""

        for update in updates:
            environment = str(update.get("environment", "")).strip()
            plant_id = str(update.get("plant", "")).strip()
            inbound_deliveries = update.get("inbound_deliveries", [])
            appt_ids = update.get("appointment_ids", [])
            trailer_id = str(update.get("trailer_id", "")).strip()
            if not (environment and plant_id and inbound_deliveries and appt_ids):
                continue

            match_found = False
            for row_idx, row in master_df.iterrows():
                row_plant = str(row.get("Plant", "")).strip()
                row_env = str(row.get("Environment", "")).strip()
                row_shipments = self._normalize_shipment_list(row.get("InboundDelivery", ""))

                if row_plant != plant_id or row_env != environment:
                    continue
                if sorted(row_shipments) != sorted(inbound_deliveries):
                    continue

                existing_appts = self._normalize_shipment_list(row.get("Appt_id", ""))
                combined = []
                seen = set()
                for appt in existing_appts + appt_ids:
                    if appt in seen:
                        continue
                    seen.add(appt)
                    combined.append(appt)
                master_df.at[row_idx, "Appt_id"] = ";".join(combined)
                if trailer_id:
                    master_df.at[row_idx, "TrailerId"] = trailer_id
                match_found = True

            if not match_found:
                logging.warning(
                    f"No MasterInput row matched Plant={plant_id}, Environment={environment}, "
                    f"InboundDelivery={';'.join(inbound_deliveries)} to store Appt_id."
                )

        try:
            with pd.ExcelWriter(
                workbook_path,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                master_df.to_excel(writer, sheet_name="MasterInput", index=False)
            logging.info(f"Updated MasterInput Appt_id values in {workbook_path}")
        except Exception as ex:
            logging.error(f"Failed to write Appt_id updates to {workbook_path}: {ex}")

    def send_appointment(self, payload_package: dict):
        environment = payload_package.get("environment")
        plant_id = str(payload_package.get("plant", "")).strip()
        payload = payload_package.get("payload", {})
        run_user = ""

        if not (environment and plant_id and payload):
            logging.error(f"Skipping malformed appointment payload package: {payload_package}")
            return {"success": False, "appointment_ids": [], "user": "", "error": "Malformed payload"}

        try:
            token_handler = Get_Token(env=environment.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()
            run_user = getattr(token_handler, "username", "")
            logging.info(f"Successfully retrieved token for {environment.upper()} / {plant_id}.")
        except Exception as ex:
            logging.error(f"Failed to retrieve token for {environment.upper()} / {plant_id}: {ex}")
            return {"success": False, "appointment_ids": [], "user": "", "error": str(ex)}

        env_handler = AWM_Env()
        env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = env_handler.get_program_url(program="Schedule_Appointment")
        if not api_url:
            logging.error(f"Could not resolve schedule appointment URL for {environment.upper()} / {plant_id}.")
            return {"success": False, "appointment_ids": [], "user": run_user, "error": "URL not resolved"}

        headers = {
            "Content-Type": "application/json",
            "selectedOrganization": plant_id,
            "selectedLocation": plant_id,
            "Authorization": f"Bearer {bearer_token}",
        }

        try:
            response = requests.post(url=api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            logging.info(
                f"Successfully scheduled appointment for {environment.upper()} / {plant_id}. "
                f"Response: {response_data.get('success', 'N/A')}"
            )
            appointment_ids = self._extract_appointment_ids(response_data)
            if appointment_ids:
                logging.info(f"Extracted appointment id(s): {', '.join(appointment_ids)}")
            else:
                logging.warning("No appointment id found in schedule response.")
            return {
                "success": True,
                "appointment_ids": appointment_ids,
                "user": run_user,
                "response_success": response_data.get("success", "N/A"),
            }
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error while scheduling appointment for {plant_id}: {http_err}")
            logging.error(f"Failed schedule payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
            if http_err.response is not None:
                logging.error(f"Status code: {http_err.response.status_code}")
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error while scheduling appointment for {plant_id}: {req_err}")
            logging.error(f"Failed schedule payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
        except json.JSONDecodeError:
            logging.error("Failed to decode schedule appointment response as JSON.")
            logging.error(f"Failed schedule payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
        except Exception as ex:
            logging.error(f"Unexpected error while scheduling appointment for {plant_id}: {ex}")
            logging.error(f"Failed schedule payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
        return {"success": False, "appointment_ids": [], "user": run_user, "error": "Request failed"}

    def send_appointments(self):
        run_started_at = datetime.now()
        run_user = ""
        success_count = 0
        failure_count = 0
        step_records = []
        generator = Appointment_Payload_Generator()
        payload_packages = generator.generate_payloads
        if not payload_packages:
            logging.warning("No appointment payloads were generated.")
            return

        grouped = defaultdict(list)
        for package in payload_packages:
            key = (package.get("environment"), str(package.get("plant", "")).strip())
            grouped[key].append(package)

        updates_for_master = []
        for (environment, plant_id), packages in grouped.items():
            logging.info(
                f"Scheduling {len(packages)} appointment payload(s) for {environment.upper()} / {plant_id}"
            )
            for package in packages:
                result = self.send_appointment(package)
                appointment_ids = result.get("appointment_ids", [])
                run_user = run_user or result.get("user", "")
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                updates_for_master.append(
                    {
                        "environment": environment,
                        "plant": plant_id,
                        "inbound_deliveries": package.get("inbound_deliveries", []),
                        "appointment_ids": appointment_ids,
                        "trailer_id": str(package.get("payload", {}).get("TrailerId", "")).strip(),
                    }
                )
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant_id,
                        "InboundDelivery": ";".join(package.get("inbound_deliveries", [])),
                        "TrailerId": str(package.get("payload", {}).get("TrailerId", "")).strip(),
                        "AppointmentIds": ";".join(appointment_ids),
                        "ApiSuccess": result.get("response_success", result.get("success", False)),
                    }
                )

        self._update_master_input_appt_id(updates_for_master)
        run_ended_at = datetime.now()
        report_path = ExecutionReportWriter().write_step_report(
            step_name="Schedule Appointment",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status="SUCCESS" if success_count and not failure_count else ("PARTIAL" if success_count else "FAILED"),
            summary={
                "TotalPayloads": len(payload_packages),
                "SuccessfulPayloads": success_count,
                "FailedPayloads": failure_count,
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")


if __name__ == "__main__":
    scheduler = Schedule_Appointment()
    scheduler.send_appointments()
