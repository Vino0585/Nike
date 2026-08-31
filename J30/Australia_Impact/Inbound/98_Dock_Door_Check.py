import json
import logging
import os
import sys
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
from Australia_Impact.Inbound.Inbound_payload_generation.Dock_Door_Check_Payload import (
    Dock_Door_Check_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Dock_Door_Check:
    ALLOWED_DOCK_DOORS = {
        *(str(door) for door in range(8001, 8010)),
        "8011",
        "8015",
        "8019",
        "8023",
    }

    @staticmethod
    def _first_allowed_dock_door_id(response_data: dict) -> str:
        results = response_data.get("data", {}).get("Results", [])
        if not results:
            return ""
        for result in results:
            if not isinstance(result, dict):
                continue
            dock_door_id = str(result.get("DockDoorId", "")).strip()
            if dock_door_id in Dock_Door_Check.ALLOWED_DOCK_DOORS:
                return dock_door_id
        return ""

    def _update_master_input_location_id(self, dock_door_by_key: dict):
        worksheet = Worksheet()
        workbook_path = Path(worksheet.master_file_path)
        try:
            master_df = pd.read_excel(workbook_path, sheet_name="MasterInput", dtype=str).fillna("")
        except Exception as ex:
            logging.error(f"Failed to read MasterInput from {workbook_path}: {ex}")
            return

        if "LocationId" not in master_df.columns:
            master_df["LocationId"] = ""

        for idx, row in master_df.iterrows():
            plant = str(row.get("Plant", "")).strip()
            environment = str(row.get("Environment", "")).strip()
            key = (plant, environment)
            dock_door_id = dock_door_by_key.get(key, "")
            if dock_door_id:
                master_df.at[idx, "LocationId"] = dock_door_id

        try:
            with pd.ExcelWriter(
                workbook_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
            ) as writer:
                master_df.to_excel(writer, sheet_name="MasterInput", index=False)
            logging.info(f"Updated MasterInput LocationId values in {workbook_path}")
        except Exception as ex:
            logging.error(f"Failed to write LocationId updates to {workbook_path}: {ex}")

    def run(self) -> bool:
        run_started_at = datetime.now()
        run_user = ""
        step_records = []
        payloads = Dock_Door_Check_Payload_Generator().generate_payloads
        if not payloads:
            logging.warning("No dock door check payloads generated.")
            return False

        dock_door_by_key = {}
        missing_dock_door_keys = []
        success_count = 0
        failure_count = 0
        for package in payloads:
            environment = str(package.get("environment", "")).strip()
            plant = str(package.get("plant", "")).strip()
            payload = package.get("payload", {})
            if not (environment and plant and payload):
                logging.error(f"Skipping malformed dock door payload package: {package}")
                missing_dock_door_keys.append((plant, environment))
                continue

            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant)
                bearer_token = token_handler.get_bearer()
                run_user = run_user or getattr(token_handler, "username", "")
            except Exception as ex:
                logging.error(f"Failed to get token for {environment}/{plant}: {ex}")
                missing_dock_door_keys.append((plant, environment))
                failure_count += 1
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant,
                        "SelectedDockDoorId": "",
                        "ReturnedDockDoorIds": "",
                        "ApiSuccess": False,
                        "Error": f"Token failure: {ex}",
                    }
                )
                continue

            env_handler = AWM_Env()
            env_handler.get_wm_host(host=environment.lower(), facility=plant)
            api_url = env_handler.get_program_url(program="Dock_Door_Check")
            if not api_url:
                logging.error(f"Could not resolve dock door check endpoint for {environment}/{plant}")
                missing_dock_door_keys.append((plant, environment))
                continue

            headers = {
                "Content-Type": "application/json",
                "selectedOrganization": plant,
                "selectedLocation": plant,
                "Authorization": f"Bearer {bearer_token}",
            }

            try:
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                dock_door_id = self._first_allowed_dock_door_id(response_data)
                result_ids = []
                for row in response_data.get("data", {}).get("Results", []):
                    if isinstance(row, dict):
                        value = str(row.get("DockDoorId", "")).strip()
                        if value:
                            result_ids.append(value)
                if dock_door_id:
                    dock_door_by_key[(plant, environment)] = dock_door_id
                    success_count += 1
                    logging.info(
                        f"Found allowed available dock door for {environment}/{plant}: {dock_door_id}"
                    )
                    step_records.append(
                        {
                            "Environment": environment,
                            "Plant": plant,
                            "SelectedDockDoorId": dock_door_id,
                            "ReturnedDockDoorIds": ";".join(result_ids),
                            "ApiSuccess": response_data.get("success", "N/A"),
                        }
                    )
                else:
                    failure_count += 1
                    logging.error(
                        "No allowed dock door available for "
                        f"{environment}/{plant}. Allowed values: "
                        f"{sorted(self.ALLOWED_DOCK_DOORS)}. Returned values: {result_ids}. "
                        "Stopping execution."
                    )
                    missing_dock_door_keys.append((plant, environment))
                    step_records.append(
                        {
                            "Environment": environment,
                            "Plant": plant,
                            "SelectedDockDoorId": "",
                            "ReturnedDockDoorIds": ";".join(result_ids),
                            "ApiSuccess": response_data.get("success", "N/A"),
                            "Error": "No allowed dock door returned",
                        }
                    )
            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error during dock door check for {environment}/{plant}: {http_err}")
                logging.error(f"Failed dock door payload for {environment}/{plant}: {json.dumps(payload)}")
                if http_err.response is not None:
                    logging.error(f"Status code: {http_err.response.status_code}")
                    logging.error(f"Response content: {http_err.response.text}")
                missing_dock_door_keys.append((plant, environment))
                failure_count += 1
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant,
                        "SelectedDockDoorId": "",
                        "ReturnedDockDoorIds": "",
                        "ApiSuccess": False,
                        "Error": f"HTTP error: {http_err}",
                    }
                )
            except requests.exceptions.RequestException as req_err:
                logging.error(f"Request error during dock door check for {environment}/{plant}: {req_err}")
                logging.error(f"Failed dock door payload for {environment}/{plant}: {json.dumps(payload)}")
                missing_dock_door_keys.append((plant, environment))
                failure_count += 1
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant,
                        "SelectedDockDoorId": "",
                        "ReturnedDockDoorIds": "",
                        "ApiSuccess": False,
                        "Error": f"Request error: {req_err}",
                    }
                )
            except json.JSONDecodeError:
                logging.error(f"Failed to decode dock door response for {environment}/{plant}.")
                logging.error(f"Failed dock door payload for {environment}/{plant}: {json.dumps(payload)}")
                missing_dock_door_keys.append((plant, environment))
                failure_count += 1
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant,
                        "SelectedDockDoorId": "",
                        "ReturnedDockDoorIds": "",
                        "ApiSuccess": False,
                        "Error": "JSON decode error",
                    }
                )
            except Exception as ex:
                logging.error(f"Unexpected error during dock door check for {environment}/{plant}: {ex}")
                logging.error(f"Failed dock door payload for {environment}/{plant}: {json.dumps(payload)}")
                missing_dock_door_keys.append((plant, environment))
                failure_count += 1
                step_records.append(
                    {
                        "Environment": environment,
                        "Plant": plant,
                        "SelectedDockDoorId": "",
                        "ReturnedDockDoorIds": "",
                        "ApiSuccess": False,
                        "Error": f"Unexpected error: {ex}",
                    }
                )

        if dock_door_by_key:
            self._update_master_input_location_id(dock_door_by_key)
        run_ended_at = datetime.now()
        report_path = ExecutionReportWriter().write_step_report(
            step_name="Dock Door Check",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status="SUCCESS" if success_count and not failure_count else ("PARTIAL" if success_count else "FAILED"),
            summary={
                "TotalPayloads": len(payloads),
                "SuccessfulPayloads": success_count,
                "FailedPayloads": failure_count,
                "AllowedDockDoors": ",".join(sorted(self.ALLOWED_DOCK_DOORS)),
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")
        if missing_dock_door_keys:
            unique_missing = sorted(set(missing_dock_door_keys))
            logging.error(
                "No dock door available for one or more Plant/Environment combinations "
                f"({unique_missing}); stopping execution."
            )
            return False
        if not dock_door_by_key:
            logging.error("No dock door ids were captured; stopping execution.")
            return False

        return True


if __name__ == "__main__":
    import sys

    ok = Dock_Door_Check().run()
    sys.exit(0 if ok else 1)
