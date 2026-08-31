import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env
from Australia_Impact.Inbound.Inbound_payload_generation.Check_In_Appointment_Payload import (
    Check_In_Appointment_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Check_In_Appointment:
    def send_check_in(self, payload_package: dict):
        environment = payload_package.get("environment")
        plant_id = str(payload_package.get("plant", "")).strip()
        payload = payload_package.get("payload", {})
        run_user = ""

        if not (environment and plant_id and payload):
            logging.error(f"Skipping malformed check-in payload package: {payload_package}")
            return {"success": False, "user": "", "error": "Malformed payload"}

        try:
            token_handler = Get_Token(env=environment.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()
            run_user = getattr(token_handler, "username", "")
            logging.info(f"Successfully retrieved token for {environment.upper()} / {plant_id}.")
        except Exception as ex:
            logging.error(f"Failed to retrieve token for {environment.upper()} / {plant_id}: {ex}")
            return {"success": False, "user": "", "error": str(ex)}

        env_handler = AWM_Env()
        env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = env_handler.get_program_url(program="Check_In_Appointment")
        if not api_url:
            logging.error(f"Could not resolve check-in URL for {environment.upper()} / {plant_id}.")
            return {"success": False, "user": run_user, "error": "URL not resolved"}

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
                f"Successfully checked in appointment for {environment.upper()} / {plant_id}. "
                f"Response: {response_data.get('success', 'N/A')}"
            )
            return {
                "success": True,
                "user": run_user,
                "response_success": response_data.get("success", "N/A"),
            }
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error while checking in appointment for {plant_id}: {http_err}")
            logging.error(f"Failed check-in payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
            if http_err.response is not None:
                logging.error(f"Status code: {http_err.response.status_code}")
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error while checking in appointment for {plant_id}: {req_err}")
            logging.error(f"Failed check-in payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
        except json.JSONDecodeError:
            logging.error("Failed to decode check-in response as JSON.")
            logging.error(f"Failed check-in payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
        except Exception as ex:
            logging.error(f"Unexpected error while checking in appointment for {plant_id}: {ex}")
            logging.error(f"Failed check-in payload for {environment.upper()} / {plant_id}: {json.dumps(payload)}")
        return {"success": False, "user": run_user, "error": "Request failed"}

    def send_all_check_ins(self):
        run_started_at = datetime.now()
        run_user = ""
        success_count = 0
        failure_count = 0
        step_records = []
        generator = Check_In_Appointment_Payload_Generator()
        payload_packages = generator.generate_payloads
        if not payload_packages:
            logging.warning("No check-in payloads were generated.")
            return

        grouped = defaultdict(list)
        for package in payload_packages:
            key = (package.get("environment"), str(package.get("plant", "")).strip())
            grouped[key].append(package)

        for (environment, plant_id), packages in grouped.items():
            logging.info(
                f"Checking in {len(packages)} appointment payload(s) for {environment.upper()} / {plant_id}"
            )
            for package in packages:
                result = self.send_check_in(package)
                run_user = run_user or result.get("user", "")
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                payload = package.get("payload", {})
                appt_info = payload.get("AppointmentInfo", {}) if isinstance(payload, dict) else {}
                trailer_info = payload.get("TrailerInfo", {}) if isinstance(payload, dict) else {}
                trailer_contents = payload.get("TrailerContents", []) if isinstance(payload, dict) else []
                inbound_values = []
                for item in trailer_contents:
                    if isinstance(item, dict):
                        shipment = str(item.get("InboundShipment", "")).strip()
                        if shipment:
                            inbound_values.append(shipment)
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant_id,
                        "AppointmentId": appt_info.get("AppointmentId", ""),
                        "TrailerId": trailer_info.get("TrailerId", ""),
                        "LocationId": payload.get("LocationId", ""),
                        "InboundDelivery": ";".join(inbound_values),
                        "ApiSuccess": result.get("response_success", result.get("success", False)),
                    }
                )

        run_ended_at = datetime.now()
        report_path = ExecutionReportWriter().write_step_report(
            step_name="Check-In Appointment",
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
    checker = Check_In_Appointment()
    checker.send_all_check_ins()
