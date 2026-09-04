import json
import logging
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)
from Australia_Impact.Inbound.Inbound_payload_generation.RF_Locate_Pallet_Payload import (
    RF_Locate_Pallet_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# -------------------------------
# User-configurable locate tuning
# -------------------------------
MAX_STAGING_THREAD_COUNT = 2
MAX_DROP_THREAD_COUNT = 2
REQUEST_TIMEOUT_SECONDS = 60

STAGING_LOCATION_BARCODE = "100801VNA1"
DROP_LOCATION_MIN_ZONE = 10
DROP_LOCATION_MAX_ZONE = 43
DROP_LOCATION_PREFIX = "10"
DROP_LOCATION_SUFFIX = "VNA011"
DROP_LOCATION_CHOICES_PER_EXECUTION = 2


class RF_Locate_Pallet:
    def __init__(self):
        self.worksheet = Worksheet()
        self.payload_generator = RF_Locate_Pallet_Payload_Generator()

    @staticmethod
    def _normalize_semicolon_list(raw_value) -> list[str]:
        seen = set()
        normalized = []
        for value in str(raw_value or "").split(";"):
            value = value.strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    @staticmethod
    def _merge_unique_semicolon(existing_value, new_values: list[str]) -> str:
        merged = []
        seen = set()
        for value in RF_Locate_Pallet._normalize_semicolon_list(existing_value) + new_values:
            value = str(value).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            merged.append(value)
        return ";".join(merged)

    @staticmethod
    def _warning_codes_from_response(response_data: dict) -> set[str]:
        try:
            error_items = (
                response_data.get("workflowVO", {})
                .get("header", {})
                .get("state", {})
                .get("errorVOList", [])
            )
            warning_codes = set()
            for item in error_items:
                if not isinstance(item, dict):
                    continue
                if str(item.get("errorCategory", "")).strip().upper() != "WARNING":
                    continue
                code = str(item.get("errorCode", "")).strip()
                if code:
                    warning_codes.add(code)
            return warning_codes
        except Exception:
            return set()

    @staticmethod
    def _error_codes_from_response(response_data: dict) -> set[str]:
        try:
            error_items = (
                response_data.get("workflowVO", {})
                .get("header", {})
                .get("state", {})
                .get("errorVOList", [])
            )
            error_codes = set()
            for item in error_items:
                if not isinstance(item, dict):
                    continue
                code = str(item.get("errorCode", "")).strip()
                if code:
                    error_codes.add(code)
            return error_codes
        except Exception:
            return set()

    @classmethod
    def _post_step(
        cls,
        url: str,
        headers: dict,
        payload: dict,
        step_name: str,
        context: str,
        allow_warning_codes: set[str] | None = None,
    ) -> dict | None:
        try:
            response = requests.post(url=url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            response_data = response.json()
            logging.info(f"{step_name} succeeded for {context}.")
            return response_data
        except requests.exceptions.HTTPError as http_err:
            response_data = None
            if http_err.response is not None:
                try:
                    response_data = http_err.response.json()
                except Exception:
                    response_data = None

            if response_data is not None and allow_warning_codes:
                warning_codes = cls._warning_codes_from_response(response_data)
                matched = warning_codes.intersection(allow_warning_codes)
                if matched:
                    logging.warning(
                        f"{step_name} returned warning(s) {sorted(matched)} for {context}; "
                        "continuing with warning override flow."
                    )
                    return response_data

            logging.error(f"{step_name} failed for {context}: {http_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
            if http_err.response is not None:
                logging.error(f"Status code: {http_err.response.status_code}")
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"{step_name} request failed for {context}: {req_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except json.JSONDecodeError:
            logging.error(f"{step_name} returned non-JSON response for {context}.")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except Exception as ex:
            logging.error(f"Unexpected error during {step_name} for {context}: {ex}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        return None

    @classmethod
    def _post_step_detailed(
        cls,
        url: str,
        headers: dict,
        payload: dict,
        step_name: str,
        context: str,
    ) -> dict:
        result = {
            "success": False,
            "response": None,
            "error_codes": set(),
            "error_message": "",
            "status_code": "",
        }
        try:
            response = requests.post(url=url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            response_data = response.json()
            logging.info(f"{step_name} succeeded for {context}.")
            result["success"] = True
            result["response"] = response_data
            return result
        except requests.exceptions.HTTPError as http_err:
            result["error_message"] = str(http_err)
            if http_err.response is not None:
                result["status_code"] = str(http_err.response.status_code)
                try:
                    response_data = http_err.response.json()
                    result["response"] = response_data
                    result["error_codes"] = cls._error_codes_from_response(response_data)
                except Exception:
                    pass
            logging.error(f"{step_name} failed for {context}: {http_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
            if http_err.response is not None:
                logging.error(f"Status code: {http_err.response.status_code}")
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            result["error_message"] = str(req_err)
            logging.error(f"{step_name} request failed for {context}: {req_err}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except json.JSONDecodeError:
            result["error_message"] = "JSON decode error"
            logging.error(f"{step_name} returned non-JSON response for {context}.")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        except Exception as ex:
            result["error_message"] = str(ex)
            logging.error(f"Unexpected error during {step_name} for {context}: {ex}")
            logging.error(f"{step_name} payload for {context}: {json.dumps(payload)}")
        return result

    def _process_staging_worker(
        self,
        pallet_id: str,
        headers: dict,
        urls: dict,
        run_user: str,
        context: str,
    ) -> dict:
        worker_context = f"{context} pallet {pallet_id}"
        try:
            scan_payload = self.payload_generator.build_staging_scan_pallet_payload(
                pallet_id=pallet_id, run_user=run_user
            )
            scan_response = self._post_step(
                urls["staging_scan"],
                headers,
                scan_payload,
                "Staging Scan Pallet",
                worker_context,
            )
            if scan_response is None:
                return {"success": False, "phase": "Staging", "pallet_id": pallet_id, "error": "Scan failed"}

            accept_payload = self.payload_generator.build_staging_accept_location_payload(
                previous_response=scan_response,
                location_barcode=STAGING_LOCATION_BARCODE,
                run_user=run_user,
            )
            accept_response = self._post_step(
                urls["staging_accept_location"],
                headers,
                accept_payload,
                "Staging Accept Location",
                worker_context,
                allow_warning_codes={"PTW::135"},
            )
            if accept_response is None:
                return {
                    "success": False,
                    "phase": "Staging",
                    "pallet_id": pallet_id,
                    "error": "Accept location failed",
                }

            confirm_payload = self.payload_generator.build_staging_confirm_put_payload(
                previous_response=accept_response,
                run_user=run_user,
            )
            confirm_response = self._post_step(
                urls["staging_confirm_put"],
                headers,
                confirm_payload,
                "Staging Confirm Put",
                worker_context,
            )
            if confirm_response is None:
                return {
                    "success": False,
                    "phase": "Staging",
                    "pallet_id": pallet_id,
                    "error": "Confirm put failed",
                }
            return {
                "success": True,
                "phase": "Staging",
                "pallet_id": pallet_id,
                "location": STAGING_LOCATION_BARCODE,
                "error": "",
            }
        except Exception as ex:
            return {"success": False, "phase": "Staging", "pallet_id": pallet_id, "error": str(ex)}

    def _process_drop_worker(
        self,
        pallet_id: str,
        drop_location: str,
        fallback_locations: list[str],
        headers: dict,
        urls: dict,
        run_user: str,
        context: str,
    ) -> dict:
        worker_context = f"{context} pallet {pallet_id}"
        try:
            scan_payload = self.payload_generator.build_drop_scan_pallet_payload(
                pallet_id=pallet_id, run_user=run_user
            )
            scan_response = self._post_step(
                urls["drop_scan"],
                headers,
                scan_payload,
                "Drop Scan Pallet",
                worker_context,
            )
            if scan_response is None:
                return {"success": False, "phase": "Drop", "pallet_id": pallet_id, "location": drop_location, "error": "Scan failed"}

            ordered_locations = [drop_location] + [loc for loc in fallback_locations if loc != drop_location]
            last_error = "Accept location failed"
            last_location = drop_location
            for attempt_idx, candidate_location in enumerate(ordered_locations, start=1):
                last_location = candidate_location
                accept_payload = self.payload_generator.build_drop_accept_location_payload(
                    previous_response=scan_response,
                    location_barcode=candidate_location,
                    run_user=run_user,
                )
                detailed = self._post_step_detailed(
                    urls["drop_accept_location"],
                    headers,
                    accept_payload,
                    "Drop Accept Location",
                    worker_context,
                )
                if detailed.get("success"):
                    return {
                        "success": True,
                        "phase": "Drop",
                        "pallet_id": pallet_id,
                        "location": candidate_location,
                        "error": "",
                    }

                error_codes = detailed.get("error_codes", set()) or set()
                last_error = detailed.get("error_message", "Accept location failed")
                if "DCI::118" in error_codes and attempt_idx < len(ordered_locations):
                    next_location = ordered_locations[attempt_idx]
                    logging.warning(
                        f"Drop location {candidate_location} is at capacity for {worker_context}; "
                        f"retrying with {next_location}."
                    )
                    continue

                break

            return {
                "success": False,
                "phase": "Drop",
                "pallet_id": pallet_id,
                "location": last_location,
                "error": last_error or "Accept location failed",
            }
        except Exception as ex:
            return {
                "success": False,
                "phase": "Drop",
                "pallet_id": pallet_id,
                "location": drop_location,
                "error": str(ex),
            }

    @staticmethod
    def _build_drop_location_pool() -> list[str]:
        return [
            f"{DROP_LOCATION_PREFIX}{zone:02d}{DROP_LOCATION_SUFFIX}"
            for zone in range(DROP_LOCATION_MIN_ZONE, DROP_LOCATION_MAX_ZONE + 1)
        ]

    def _update_master_input_drop_locations(self, updates: list[dict]):
        if not updates:
            return

        workbook_path = Path(self.worksheet.master_file_path)
        if not workbook_path.exists():
            logging.error(f"Worksheet not found for drop location updates: {workbook_path}")
            return

        try:
            master_df = pd.read_excel(workbook_path, sheet_name="MasterInput", dtype=str).fillna("")
        except Exception as ex:
            logging.error(f"Failed to read MasterInput from {workbook_path}: {ex}")
            return

        if "DropLocation" not in master_df.columns:
            master_df["DropLocation"] = ""

        for update in updates:
            environment = str(update.get("environment", "")).strip()
            plant = str(update.get("plant", "")).strip()
            pallet_ids = update.get("pallet_ids", [])
            drop_locations = self._normalize_semicolon_list(";".join(update.get("drop_locations", [])))
            if not (environment and plant and pallet_ids and drop_locations):
                continue

            matched = False
            for idx, row in master_df.iterrows():
                row_env = str(row.get("Environment", "")).strip()
                row_plant = str(row.get("Plant", "")).strip()
                row_pallets = self._normalize_semicolon_list(
                    str(row.get("PalletId", "")).strip()
                    or str(row.get("PalletID", "")).strip()
                    or str(row.get("Palletid", "")).strip()
                )
                pallet_overlap = bool(set(row_pallets).intersection(set(pallet_ids)))
                if row_env != environment or row_plant != plant or not pallet_overlap:
                    continue

                master_df.at[idx, "DropLocation"] = self._merge_unique_semicolon(
                    row.get("DropLocation", ""),
                    drop_locations,
                )
                matched = True

            if not matched:
                logging.warning(
                    f"No MasterInput row matched Plant={plant}, Environment={environment} for pallet drop writeback."
                )

        try:
            with pd.ExcelWriter(
                workbook_path,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                master_df.to_excel(writer, sheet_name="MasterInput", index=False)
            logging.info(f"Updated MasterInput DropLocation values in {workbook_path}")
        except Exception as ex:
            logging.error(f"Failed to write DropLocation updates to {workbook_path}: {ex}")

    def run(self) -> bool:
        run_started_at = datetime.now()
        run_user = ""
        step_records = []
        all_success = True
        success_count = 0
        failure_count = 0
        drop_location_updates = []

        rows = self.worksheet.rf_locate_pallet_worksheet_extract()
        if not rows:
            logging.error("No valid rows found for RF pallet locate in MasterInput.")
            run_ended_at = datetime.now()
            ExecutionReportWriter().write_step_report(
                step_name="RF Locate Pallet",
                run_user=os.getenv("USER", ""),
                started_at=run_started_at,
                ended_at=run_ended_at,
                status="FAILED",
                summary={"TotalPallets": 0, "SuccessfulTransactions": 0, "FailedTransactions": 0},
                records=[{"Error": "No valid rows found for RF pallet locate in MasterInput."}],
            )
            return False

        all_drop_locations = self._build_drop_location_pool()
        selected_drop_locations = random.sample(
            all_drop_locations,
            k=min(DROP_LOCATION_CHOICES_PER_EXECUTION, len(all_drop_locations)),
        )
        logging.info(f"Selected drop location pool for this execution: {selected_drop_locations}")

        total_pallets = 0
        for row in rows:
            environment = str(row.get("Environment", "")).strip()
            plant = str(row.get("Plant", "")).strip()
            pallet_ids = row.get("PalletIDs", [])
            if not (environment and plant and pallet_ids):
                logging.error(f"Skipping incomplete RF locate row: {row}")
                all_success = False
                continue

            context = f"{environment.upper()}/{plant}"
            total_pallets += len(pallet_ids)

            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant)
                bearer_token = token_handler.get_bearer()
                run_user = str(getattr(token_handler, "username", "")).strip()
            except Exception as ex:
                logging.error(f"Token fetch failed for {context}: {ex}")
                all_success = False
                failure_count += 1
                step_records.append(
                    {"Context": context, "Phase": "Auth", "Result": "FAILED", "Error": str(ex)}
                )
                continue

            env_handler = AWM_Env()
            env_handler.get_wm_host(host=environment.lower(), facility=plant)
            urls = {
                "staging_scan": env_handler.get_program_url("RF_Locate_Staging_Pallet_Scan"),
                "staging_accept_location": env_handler.get_program_url("RF_Locate_Staging_Accept_Location"),
                "staging_confirm_put": env_handler.get_program_url("RF_Locate_Staging_Confirm_Put"),
                "drop_scan": env_handler.get_program_url("RF_Locate_Drop_Pallet_Scan"),
                "drop_accept_location": env_handler.get_program_url("RF_Locate_Drop_Accept_Location"),
            }
            if not all(urls.values()):
                logging.error(f"RF locate endpoint resolution failed for {context}.")
                all_success = False
                continue

            headers = {
                "authorization": f"Bearer {bearer_token}",
                "content-type": "application/json",
                "selectedlocation": plant,
                "selectedorganization": plant,
            }

            staging_workers = min(MAX_STAGING_THREAD_COUNT, max(len(pallet_ids), 1))
            logging.info(
                f"Running staging locate for {context}: pallets={len(pallet_ids)} threads={staging_workers}"
            )
            staging_results = []
            with ThreadPoolExecutor(max_workers=staging_workers) as executor:
                futures = [
                    executor.submit(
                        self._process_staging_worker,
                        pallet_id,
                        headers,
                        urls,
                        run_user,
                        context,
                    )
                    for pallet_id in pallet_ids
                ]
                for future in as_completed(futures):
                    staging_results.append(future.result())

            row_staging_success = all(result.get("success") for result in staging_results)
            for result in staging_results:
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                    all_success = False
                step_records.append(
                    {
                        "Context": context,
                        "Phase": "Locate to VNA Staging",
                        "PalletId": result.get("pallet_id", ""),
                        "Location": result.get("location", STAGING_LOCATION_BARCODE),
                        "Result": "SUCCESS" if result.get("success") else "FAILED",
                        "Error": result.get("error", ""),
                        "ThreadMode": f"{staging_workers} thread(s)",
                    }
                )

            if not row_staging_success:
                logging.error(f"Staging locate failed for one or more pallets in {context}.")
                break

            pallet_drop_assignments = {
                pallet_id: random.choice(selected_drop_locations) for pallet_id in pallet_ids
            }
            drop_workers = min(MAX_DROP_THREAD_COUNT, max(len(pallet_ids), 1))
            logging.info(
                f"Running drop locate for {context}: pallets={len(pallet_ids)} threads={drop_workers}"
            )
            drop_results = []
            with ThreadPoolExecutor(max_workers=drop_workers) as executor:
                futures = [
                    executor.submit(
                        self._process_drop_worker,
                        pallet_id,
                        pallet_drop_assignments[pallet_id],
                        selected_drop_locations,
                        headers,
                        urls,
                        run_user,
                        context,
                    )
                    for pallet_id in pallet_ids
                ]
                for future in as_completed(futures):
                    drop_results.append(future.result())

            for result in drop_results:
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                    all_success = False
                step_records.append(
                    {
                        "Context": context,
                        "Phase": "Locate to Drop Location",
                        "PalletId": result.get("pallet_id", ""),
                        "Location": result.get("location", ""),
                        "Result": "SUCCESS" if result.get("success") else "FAILED",
                        "Error": result.get("error", ""),
                        "ThreadMode": f"{drop_workers} thread(s)",
                    }
                )

            successful_drop_locations = [
                str(result.get("location", "")).strip()
                for result in drop_results
                if result.get("success") and str(result.get("location", "")).strip()
            ]
            if successful_drop_locations:
                drop_location_updates.append(
                    {
                        "environment": environment,
                        "plant": plant,
                        "pallet_ids": pallet_ids,
                        "drop_locations": successful_drop_locations,
                    }
                )

            if not all(result.get("success") for result in drop_results):
                logging.error(f"Drop locate failed for one or more pallets in {context}.")
                break

        self._update_master_input_drop_locations(drop_location_updates)

        run_ended_at = datetime.now()
        status = "SUCCESS" if all_success else ("PARTIAL" if success_count else "FAILED")
        report_path = ExecutionReportWriter().write_step_report(
            step_name="RF Locate Pallet",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status=status,
            summary={
                "TotalPallets": total_pallets,
                "SuccessfulTransactions": success_count,
                "FailedTransactions": failure_count,
                "StagingLocation": STAGING_LOCATION_BARCODE,
                "DropLocationChoicesUsed": ";".join(selected_drop_locations),
                "MaxStagingThreadCount": MAX_STAGING_THREAD_COUNT,
                "MaxDropThreadCount": MAX_DROP_THREAD_COUNT,
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")

        if all_success:
            logging.info("RF Locate Pallet completed successfully.")
        return all_success


if __name__ == "__main__":
    ok = RF_Locate_Pallet().run()
    sys.exit(0 if ok else 1)
