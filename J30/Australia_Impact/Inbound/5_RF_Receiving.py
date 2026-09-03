import json
import logging
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from pathlib import Path

import pandas as pd
import requests

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env
from Australia_Impact.Inbound.Inbound_payload_generation.RF_Receiving_Payload import (
    RF_Receiving_Payload_Generator,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------
# User-configurable RF tuning
# ---------------------------
LPNS_PER_PALLET = 20
MAX_THREAD_COUNT = 6
REQUEST_TIMEOUT_SECONDS = 60
MIN_ACTION_DELAY_SECONDS = 0.20
MAX_ACTION_DELAY_SECONDS = 0.80


class WorkerState(str, Enum):
    INIT = "INIT"
    DOCK_ACCEPTED = "DOCK_ACCEPTED"
    SHIPMENT_ACCEPTED = "SHIPMENT_ACCEPTED"
    LPN_ACCEPTED = "LPN_ACCEPTED"
    PALLET_ACCEPTED = "PALLET_ACCEPTED"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class WorkerStateMachine:
    ALLOWED_TRANSITIONS = {
        WorkerState.INIT: {WorkerState.DOCK_ACCEPTED, WorkerState.FAILED},
        WorkerState.DOCK_ACCEPTED: {WorkerState.SHIPMENT_ACCEPTED, WorkerState.FAILED},
        WorkerState.SHIPMENT_ACCEPTED: {WorkerState.LPN_ACCEPTED, WorkerState.COMPLETE, WorkerState.FAILED},
        WorkerState.LPN_ACCEPTED: {WorkerState.PALLET_ACCEPTED, WorkerState.FAILED},
        WorkerState.PALLET_ACCEPTED: {WorkerState.LPN_ACCEPTED, WorkerState.COMPLETE, WorkerState.FAILED},
        WorkerState.COMPLETE: set(),
        WorkerState.FAILED: set(),
    }

    def __init__(self):
        self.state = WorkerState.INIT

    def transition(self, target_state: WorkerState):
        if target_state not in self.ALLOWED_TRANSITIONS[self.state]:
            raise RuntimeError(
                f"Invalid worker state transition: {self.state.value} -> {target_state.value}"
            )
        self.state = target_state


class RF_Receiving:
    def __init__(self):
        self.payload_generator = RF_Receiving_Payload_Generator()
        self.worksheet = Worksheet()
        self._pallet_lock = threading.Lock()

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

    @staticmethod
    def _randomized_delay():
        sleep_time = random.uniform(MIN_ACTION_DELAY_SECONDS, MAX_ACTION_DELAY_SECONDS)
        time.sleep(sleep_time)

    def _next_pallet_id_threadsafe(self) -> str:
        with self._pallet_lock:
            return self.payload_generator.next_pallet_id()

    @staticmethod
    def _chunk_list(values: list[str], chunk_size: int) -> list[list[str]]:
        if chunk_size <= 0:
            chunk_size = 1
        return [values[idx:idx + chunk_size] for idx in range(0, len(values), chunk_size)]

    @staticmethod
    def _derive_thread_count(pallet_count: int) -> int:
        if pallet_count <= 1:
            return 1
        return min(MAX_THREAD_COUNT, pallet_count)

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

    @classmethod
    def _merge_unique_semicolon(cls, existing_value, new_values: list[str]) -> str:
        merged = []
        seen = set()
        for value in cls._normalize_semicolon_list(existing_value) + cls._normalize_semicolon_list(";".join(new_values)):
            if value in seen:
                continue
            seen.add(value)
            merged.append(value)
        return ";".join(merged)

    def _update_master_input_pallet_ids(self, updates: list[dict]):
        if not updates:
            return

        worksheet = Worksheet()
        workbook_path = Path(worksheet.master_file_path)
        if not workbook_path.exists():
            logging.error(f"Worksheet not found for pallet updates: {workbook_path}")
            return

        try:
            master_df = pd.read_excel(workbook_path, sheet_name="MasterInput", dtype=str).fillna("")
        except Exception as ex:
            logging.error(f"Failed to read MasterInput from {workbook_path}: {ex}")
            return

        if master_df.empty:
            logging.warning("MasterInput is empty. No pallet updates were written.")
            return

        pallet_column = "PalletId"
        if "PalletId" not in master_df.columns and "PalletID" in master_df.columns:
            pallet_column = "PalletID"
        if pallet_column not in master_df.columns:
            master_df[pallet_column] = ""

        for update in updates:
            environment = str(update.get("environment", "")).strip()
            plant = str(update.get("plant", "")).strip()
            shipment_id = str(update.get("shipment_id", "")).strip()
            pallet_ids = self._normalize_semicolon_list(";".join(update.get("pallet_ids", [])))
            if not (environment and plant and shipment_id and pallet_ids):
                continue

            matched = False
            for row_idx, row in master_df.iterrows():
                row_env = str(row.get("Environment", "")).strip()
                row_plant = str(row.get("Plant", "")).strip()
                row_shipments = self._normalize_semicolon_list(row.get("InboundDelivery", ""))
                if row_env != environment or row_plant != plant or shipment_id not in row_shipments:
                    continue

                master_df.at[row_idx, pallet_column] = self._merge_unique_semicolon(
                    row.get(pallet_column, ""),
                    pallet_ids,
                )
                matched = True

            if not matched:
                logging.warning(
                    f"No MasterInput row matched Plant={plant}, Environment={environment}, "
                    f"Shipment={shipment_id} for pallet writeback."
                )

        try:
            with pd.ExcelWriter(
                workbook_path,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                master_df.to_excel(writer, sheet_name="MasterInput", index=False)
            logging.info(f"Updated MasterInput {pallet_column} values in {workbook_path}")
        except Exception as ex:
            logging.error(f"Failed to write pallet updates to {workbook_path}: {ex}")

    def _process_pallet_worker(
        self,
        environment: str,
        plant: str,
        shipment_id: str,
        dock_door_id: str,
        headers: dict,
        urls: dict,
        lpn_chunk: list[str],
        pallet_id: str,
        run_user: str,
        worker_idx: int,
    ) -> dict:
        shipment_context = f"{environment.upper()}/{plant} shipment {shipment_id} worker-{worker_idx}"
        machine = WorkerStateMachine()
        lpn_processed = 0
        failure_step = ""
        error_message = ""
        success_steps = 0
        failed_steps = 0

        try:
            dock_payload = self.payload_generator.build_accept_dock_door_payload(
                dock_door_id=dock_door_id, run_user=run_user
            )
            dock_response = self._post_step(
                urls["dock"], headers, dock_payload, "AcceptDockDoor", shipment_context
            )
            if dock_response is None:
                machine.transition(WorkerState.FAILED)
                failure_step = "AcceptDockDoor"
                failed_steps += 1
                return {
                    "success": False,
                    "worker": worker_idx,
                    "pallet_id": pallet_id,
                    "lpn_processed": lpn_processed,
                    "failure_step": failure_step,
                    "error": "Dock door acceptance failed",
                    "success_steps": success_steps,
                    "failed_steps": failed_steps,
                }
            machine.transition(WorkerState.DOCK_ACCEPTED)
            success_steps += 1
            self._randomized_delay()

            shipment_payload = self.payload_generator.build_accept_shipment_payload(
                previous_response=dock_response,
                shipment_id=shipment_id,
                run_user=run_user,
            )
            shipment_response = self._post_step(
                urls["shipment"], headers, shipment_payload, "AcceptShipment", shipment_context
            )
            if shipment_response is None:
                machine.transition(WorkerState.FAILED)
                failure_step = "AcceptShipment"
                failed_steps += 1
                return {
                    "success": False,
                    "worker": worker_idx,
                    "pallet_id": pallet_id,
                    "lpn_processed": lpn_processed,
                    "failure_step": failure_step,
                    "error": "Shipment acceptance failed",
                    "success_steps": success_steps,
                    "failed_steps": failed_steps,
                }
            machine.transition(WorkerState.SHIPMENT_ACCEPTED)
            success_steps += 1
            self._randomized_delay()

            lpn_state_payload = shipment_response
            for lpn_index, lpn_id in enumerate(lpn_chunk):
                lpn_payload = self.payload_generator.build_accept_lpn_payload(
                    previous_response=lpn_state_payload,
                    lpn_id=lpn_id,
                    run_user=run_user,
                )
                lpn_response = self._post_step(
                    urls["lpn"], headers, lpn_payload, "AcceptLPN", shipment_context
                )
                if lpn_response is None:
                    machine.transition(WorkerState.FAILED)
                    failure_step = "AcceptLPN"
                    failed_steps += 1
                    return {
                        "success": False,
                        "worker": worker_idx,
                        "pallet_id": pallet_id,
                        "lpn_processed": lpn_processed,
                        "failure_step": failure_step,
                        "error": f"LPN acceptance failed for {lpn_id}",
                        "success_steps": success_steps,
                        "failed_steps": failed_steps,
                    }
                machine.transition(WorkerState.LPN_ACCEPTED)
                success_steps += 1
                lpn_processed += 1
                self._randomized_delay()

                pallet_payload = self.payload_generator.build_accept_to_pallet_payload(
                    previous_response=lpn_response,
                    pallet_id=pallet_id,
                    run_user=run_user,
                )
                pallet_response = self._post_step(
                    urls["pallet"], headers, pallet_payload, "AcceptToPallet", shipment_context
                )
                if pallet_response is None:
                    machine.transition(WorkerState.FAILED)
                    failure_step = "AcceptToPallet"
                    failed_steps += 1
                    return {
                        "success": False,
                        "worker": worker_idx,
                        "pallet_id": pallet_id,
                        "lpn_processed": lpn_processed,
                        "failure_step": failure_step,
                        "error": f"Palletization failed for {lpn_id}",
                        "success_steps": success_steps,
                        "failed_steps": failed_steps,
                    }
                machine.transition(WorkerState.PALLET_ACCEPTED)
                success_steps += 1
                self._randomized_delay()

                if lpn_index < len(lpn_chunk) - 1:
                    next_lpn_payload = self.payload_generator.extract_next_accept_lpn_payload(
                        pallet_response, run_user=run_user
                    )
                    if next_lpn_payload is None:
                        machine.transition(WorkerState.FAILED)
                        failure_step = "NextAcceptLPNPayloadDerivation"
                        failed_steps += 1
                        return {
                            "success": False,
                            "worker": worker_idx,
                            "pallet_id": pallet_id,
                            "lpn_processed": lpn_processed,
                            "failure_step": failure_step,
                            "error": f"Could not derive next LPN payload after {lpn_id}",
                            "success_steps": success_steps,
                            "failed_steps": failed_steps,
                        }
                    lpn_state_payload = next_lpn_payload

            machine.transition(WorkerState.COMPLETE)
            return {
                "success": True,
                "worker": worker_idx,
                "pallet_id": pallet_id,
                "lpn_processed": lpn_processed,
                "failure_step": "",
                "error": "",
                "success_steps": success_steps,
                "failed_steps": failed_steps,
            }
        except Exception as ex:
            error_message = str(ex)
            try:
                machine.transition(WorkerState.FAILED)
            except Exception:
                pass
            return {
                "success": False,
                "worker": worker_idx,
                "pallet_id": pallet_id,
                "lpn_processed": lpn_processed,
                "failure_step": failure_step or "StateMachineOrWorkerError",
                "error": error_message,
                "success_steps": success_steps,
                "failed_steps": failed_steps + 1,
            }

    def run(self) -> bool:
        run_started_at = datetime.now()
        run_user = ""
        step_records = []
        pallet_updates = []
        success_count = 0
        failure_count = 0

        rows = self.worksheet.rf_receiving_worksheet_extract()
        if not rows:
            logging.error("No valid RF receiving rows found in MasterInput.")
            run_ended_at = datetime.now()
            ExecutionReportWriter().write_step_report(
                step_name="RF Receiving",
                run_user=os.getenv("USER", ""),
                started_at=run_started_at,
                ended_at=run_ended_at,
                status="FAILED",
                summary={"TotalShipments": 0, "ProcessedShipments": 0, "FailedShipments": 0},
                records=[{"Error": "No valid RF receiving rows found in MasterInput."}],
            )
            return False

        all_success = True
        shipment_total = 0
        shipment_processed = 0
        shipment_failed = 0
        for row in rows:
            environment = str(row.get("Environment", "")).strip()
            plant = str(row.get("Plant", "")).strip()
            dock_door_id = str(row.get("LocationId", "")).strip()
            shipments = row.get("InboundDeliveries", [])
            lpn_ids = row.get("LPNIDs", [])

            if not (environment and plant and dock_door_id and shipments and lpn_ids):
                logging.error(f"Skipping incomplete RF row: {row}")
                all_success = False
                continue

            context = f"{environment.upper()}/{plant}"
            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant)
                bearer_token = token_handler.get_bearer()
                run_user = str(getattr(token_handler, "username", "")).strip()
            except Exception as ex:
                logging.error(f"Token fetch failed for {context}: {ex}")
                all_success = False
                failure_count += 1
                step_records.append(
                    {
                        "Context": context,
                        "Result": "FAILED",
                        "FailedAt": "Token",
                        "Error": str(ex),
                    }
                )
                continue

            env_handler = AWM_Env()
            env_handler.get_wm_host(host=environment.lower(), facility=plant)
            urls = {
                "dock": env_handler.get_program_url("RF_Accept_Dock_Door"),
                "shipment": env_handler.get_program_url("RF_Accept_Shipment"),
                "lpn": env_handler.get_program_url("RF_Accept_LPN"),
                "pallet": env_handler.get_program_url("RF_Accept_To_Pallet"),
            }
            if not all(urls.values()):
                logging.error(f"RF endpoint resolution failed for {context}.")
                all_success = False
                continue

            headers = {
                "authorization": f"Bearer {bearer_token}",
                "content-type": "application/json",
                "selectedlocation": plant,
                "selectedorganization": plant,
            }

            for shipment_id in shipments:
                shipment_total += 1
                shipment_context = f"{context} shipment {shipment_id}"
                logging.info(f"Starting RF receiving loop for {shipment_context}.")
                pallet_chunks = self._chunk_list(lpn_ids, LPNS_PER_PALLET)
                pallet_count = len(pallet_chunks)
                thread_count = self._derive_thread_count(pallet_count)
                pallet_ids = [self._next_pallet_id_threadsafe() for _ in pallet_chunks]
                logging.info(
                    f"RF worker scaling for {shipment_context}: "
                    f"LPNs={len(lpn_ids)} Pallets={pallet_count} Threads={thread_count}"
                )

                worker_results = []
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = []
                    for worker_idx, lpn_chunk in enumerate(pallet_chunks, start=1):
                        futures.append(
                            executor.submit(
                                self._process_pallet_worker,
                                environment,
                                plant,
                                shipment_id,
                                dock_door_id,
                                headers,
                                urls,
                                lpn_chunk,
                                pallet_ids[worker_idx - 1],
                                run_user,
                                worker_idx,
                            )
                        )

                    for future in as_completed(futures):
                        worker_results.append(future.result())

                shipment_ok = all(result.get("success") for result in worker_results)
                if shipment_ok:
                    shipment_processed += 1
                else:
                    shipment_failed += 1
                    all_success = False

                successful_pallet_ids = [
                    str(result.get("pallet_id", "")).strip()
                    for result in worker_results
                    if result.get("success") and str(result.get("pallet_id", "")).strip()
                ]
                if successful_pallet_ids:
                    pallet_updates.append(
                        {
                            "environment": environment,
                            "plant": plant,
                            "shipment_id": shipment_id,
                            "pallet_ids": successful_pallet_ids,
                        }
                    )

                for result in worker_results:
                    success_count += int(result.get("success_steps", 0))
                    failure_count += int(result.get("failed_steps", 0))
                    step_records.append(
                        {
                            "Context": shipment_context,
                            "DockDoor": dock_door_id,
                            "Worker": result.get("worker"),
                            "PalletId": result.get("pallet_id", ""),
                            "Result": "SUCCESS" if result.get("success") else "FAILED",
                            "ProcessedLPNCount": result.get("lpn_processed", 0),
                            "FailedAt": result.get("failure_step", ""),
                            "Error": result.get("error", ""),
                            "ThreadMode": f"{thread_count} thread(s)",
                        }
                    )

                if not shipment_ok:
                    break

                logging.info(f"Completed RF receiving loop for {shipment_context}.")

            if not all_success:
                break

        self._update_master_input_pallet_ids(pallet_updates)

        run_ended_at = datetime.now()
        report_status = "SUCCESS" if all_success else ("PARTIAL" if success_count else "FAILED")
        report_path = ExecutionReportWriter().write_step_report(
            step_name="RF Receiving",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status=report_status,
            summary={
                "TotalShipments": shipment_total,
                "ProcessedShipments": shipment_processed,
                "FailedShipments": shipment_failed,
                "LPNsPerPallet": LPNS_PER_PALLET,
                "MaxThreadCount": MAX_THREAD_COUNT,
                "SuccessfulApiSteps": success_count,
                "FailedApiSteps": failure_count,
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")

        if all_success:
            logging.info("RF Receiving completed successfully.")
        return all_success


if __name__ == "__main__":
    ok = RF_Receiving().run()
    sys.exit(0 if ok else 1)