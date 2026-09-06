import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

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
from Australia_Impact.Inbound.Inbound_payload_generation.RF_Putaway_Carton_Storage_Payload import (
    RF_Putaway_Carton_Storage_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# User-configurable putaway settings.
MAX_PUTAWAY_THREAD_COUNT = 3
REQUEST_TIMEOUT_SECONDS = 60
MAX_PALLET_LOOP_ITERATIONS = 500


class RF_Putaway_Carton_Storage:
    def __init__(self):
        self.worksheet = Worksheet()
        self.payload_generator = RF_Putaway_Carton_Storage_Payload_Generator()

    @staticmethod
    def _state(payload: dict) -> dict:
        return (
            payload.get("workflowVO", {})
            .get("header", {})
            .get("state", {})
        )

    @staticmethod
    def _current_state(payload: dict) -> str:
        return str(
            payload.get("workflowVO", {})
            .get("header", {})
            .get("currentState", "")
        ).strip()

    @staticmethod
    def _post_step(url: str, headers: dict, payload: dict, step_name: str, context: str) -> dict | None:
        try:
            response = requests.post(url=url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            response_data = response.json()
            logging.info(f"{step_name} succeeded for {context}.")
            return response_data
        except requests.exceptions.HTTPError as http_err:
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

    def _process_pallet_worker(
        self,
        pallet_id: str,
        headers: dict,
        urls: dict,
        run_user: str,
        context: str,
    ) -> dict:
        worker_context = f"{context} pallet {pallet_id}"
        cartons_scanned = 0
        try:
            pallet_payload = self.payload_generator.build_pallet_scan_payload(
                pallet_id=pallet_id,
                run_user=run_user,
            )
            pallet_response = self._post_step(
                urls["pallet_scan"],
                headers,
                pallet_payload,
                "Putaway Pallet Scan",
                worker_context,
            )
            if pallet_response is None:
                return {
                    "success": False,
                    "pallet_id": pallet_id,
                    "cartons_scanned": cartons_scanned,
                    "failed_step": "PalletScan",
                    "error": "Pallet scan failed",
                }

            current_payload = pallet_response
            for _ in range(MAX_PALLET_LOOP_ITERATIONS):
                current_state = self._current_state(current_payload)
                if current_state == "AcceptContainerForSystemDirectedPutaway":
                    # Loop completed: backend moved to next pallet prompt.
                    return {
                        "success": True,
                        "pallet_id": pallet_id,
                        "cartons_scanned": cartons_scanned,
                        "failed_step": "",
                        "error": "",
                    }

                location_payload = self.payload_generator.build_scan_location_payload(
                    previous_response=current_payload,
                    run_user=run_user,
                )
                location_barcode = str(self._state(location_payload).get("scannedLocationBarcode", "")).strip()
                if not location_barcode:
                    return {
                        "success": False,
                        "pallet_id": pallet_id,
                        "cartons_scanned": cartons_scanned,
                        "failed_step": "ScanLocationPayload",
                        "error": "locationVO.barcode is missing in scan-location payload",
                    }

                location_response = self._post_step(
                    urls["scan_location"],
                    headers,
                    location_payload,
                    "Putaway Scan Location",
                    worker_context,
                )
                if location_response is None:
                    return {
                        "success": False,
                        "pallet_id": pallet_id,
                        "cartons_scanned": cartons_scanned,
                        "failed_step": "ScanLocation",
                        "error": "Scan location request failed",
                    }

                carton_payload = self.payload_generator.build_carton_scan_payload(
                    previous_response=location_response,
                    run_user=run_user,
                )
                carton_barcode = str(self._state(carton_payload).get("scannedContainerBarcode", "")).strip()
                if not carton_barcode:
                    return {
                        "success": False,
                        "pallet_id": pallet_id,
                        "cartons_scanned": cartons_scanned,
                        "failed_step": "CartonScanPayload",
                        "error": "containerId is missing in carton-scan payload",
                    }

                carton_response = self._post_step(
                    urls["scan_carton"],
                    headers,
                    carton_payload,
                    "Putaway Carton Scan",
                    worker_context,
                )
                if carton_response is None:
                    return {
                        "success": False,
                        "pallet_id": pallet_id,
                        "cartons_scanned": cartons_scanned,
                        "failed_step": "CartonScan",
                        "error": "Carton scan request failed",
                    }
                cartons_scanned += 1
                current_payload = carton_response

            return {
                "success": False,
                "pallet_id": pallet_id,
                "cartons_scanned": cartons_scanned,
                "failed_step": "LoopGuard",
                "error": f"Exceeded max iterations ({MAX_PALLET_LOOP_ITERATIONS}) for pallet flow",
            }
        except Exception as ex:
            return {
                "success": False,
                "pallet_id": pallet_id,
                "cartons_scanned": cartons_scanned,
                "failed_step": "UnexpectedError",
                "error": str(ex),
            }

    def run(self) -> bool:
        run_started_at = datetime.now()
        run_user = ""
        all_success = True
        success_count = 0
        failure_count = 0
        total_pallets = 0
        step_records = []

        rows = self.worksheet.rf_putaway_carton_storage_extract()
        if not rows:
            logging.error("No valid rows found for RF putaway carton storage in MasterInput.")
            run_ended_at = datetime.now()
            ExecutionReportWriter().write_step_report(
                step_name="RF Putaway Carton Storage",
                run_user=os.getenv("USER", ""),
                started_at=run_started_at,
                ended_at=run_ended_at,
                status="FAILED",
                summary={"TotalPallets": 0, "SuccessfulPallets": 0, "FailedPallets": 0},
                records=[{"Error": "No valid rows found for RF putaway carton storage in MasterInput."}],
            )
            return False

        for row in rows:
            environment = str(row.get("Environment", "")).strip()
            plant = str(row.get("Plant", "")).strip()
            pallet_ids = row.get("PalletIDs", [])
            if not (environment and plant and pallet_ids):
                logging.error(f"Skipping incomplete RF putaway row: {row}")
                all_success = False
                continue
            total_pallets += len(pallet_ids)
            context = f"{environment.upper()}/{plant}"

            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant)
                bearer_token = token_handler.get_bearer()
                run_user = str(getattr(token_handler, "username", "")).strip()
            except Exception as ex:
                logging.error(f"Token fetch failed for {context}: {ex}")
                all_success = False
                failure_count += len(pallet_ids)
                step_records.append(
                    {
                        "Context": context,
                        "PalletId": ";".join(pallet_ids),
                        "Result": "FAILED",
                        "FailedAt": "Token",
                        "Error": str(ex),
                        "ThreadMode": "N/A",
                    }
                )
                continue

            env_handler = AWM_Env()
            env_handler.get_wm_host(host=environment.lower(), facility=plant)
            urls = {
                "pallet_scan": env_handler.get_program_url("RF_Putaway_Carton_Pallet_Scan"),
                "scan_location": env_handler.get_program_url("RF_Putaway_Carton_Scan_Location"),
                "scan_carton": env_handler.get_program_url("RF_Putaway_Carton_Scan_Carton"),
            }
            if not all(urls.values()):
                logging.error(f"RF putaway endpoint resolution failed for {context}.")
                all_success = False
                failure_count += len(pallet_ids)
                continue

            headers = {
                "authorization": f"Bearer {bearer_token}",
                "content-type": "application/json",
                "selectedlocation": plant,
                "selectedorganization": plant,
            }

            thread_count = min(MAX_PUTAWAY_THREAD_COUNT, max(len(pallet_ids), 1))
            logging.info(
                f"Running RF putaway carton storage for {context}: "
                f"pallets={len(pallet_ids)} threads={thread_count}"
            )

            worker_results = []
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [
                    executor.submit(
                        self._process_pallet_worker,
                        pallet_id,
                        headers,
                        urls,
                        run_user,
                        context,
                    )
                    for pallet_id in pallet_ids
                ]
                for future in as_completed(futures):
                    worker_results.append(future.result())

            for result in worker_results:
                if result.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                    all_success = False
                step_records.append(
                    {
                        "Context": context,
                        "PalletId": result.get("pallet_id", ""),
                        "Result": "SUCCESS" if result.get("success") else "FAILED",
                        "CartonsScanned": result.get("cartons_scanned", 0),
                        "FailedAt": result.get("failed_step", ""),
                        "Error": result.get("error", ""),
                        "ThreadMode": f"{thread_count} thread(s)",
                    }
                )

            if not all(result.get("success") for result in worker_results):
                break

        run_ended_at = datetime.now()
        status = "SUCCESS" if all_success else ("PARTIAL" if success_count else "FAILED")
        report_path = ExecutionReportWriter().write_step_report(
            step_name="RF Putaway Carton Storage",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status=status,
            summary={
                "TotalPallets": total_pallets,
                "SuccessfulPallets": success_count,
                "FailedPallets": failure_count,
                "MaxThreadCount": MAX_PUTAWAY_THREAD_COUNT,
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")
        if all_success:
            logging.info("RF Putaway Carton Storage completed successfully.")
        return all_success


if __name__ == "__main__":
    ok = RF_Putaway_Carton_Storage().run()
    sys.exit(0 if ok else 1)
