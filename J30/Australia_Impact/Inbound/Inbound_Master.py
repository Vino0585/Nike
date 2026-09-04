import logging
import pandas as pd
import time
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import os

# Ensure repository root is on sys.path so `Australia_Impact` imports work when file runs directly
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["NIKE_DISABLE_SSL_VERIFY"] = "true"

from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)


class inbound_master_step:

    def __init__(self):
        """Initialize inbound master for Australia-specific flow orchestration."""
        self.worksheet_extractor = Worksheet()
        self.inbound_dir = CURRENT_DIR

    def _run_script(self, script_name: str, step_label: str):
        script_path = self.inbound_dir / script_name
        if not script_path.exists():
            logging.error(f"{step_label} script not found: {script_path}")
            return False
        logging.info(f"{step_label} Started Successfully")
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{PROJECT_ROOT}:{existing_pythonpath}" if existing_pythonpath else str(PROJECT_ROOT)
        try:
            subprocess.run(
                [sys.executable, str(script_path)],
                check=True,
                cwd=str(PROJECT_ROOT),
                env=env,
            )
            logging.info(f"{step_label} Completed Successfully")
            return True
        except subprocess.CalledProcessError as ex:
            logging.error(f"{step_label} failed with exit code {ex.returncode}")
            return False

    def is_no_or_empty(self, value):
        return value == 'N' or pd.isna(value) or value is None

    def call_asn_creation_program(self):
        if not self._run_script("1_ASN_Creation.py", "ASN Creation Program"):
            raise RuntimeError("ASN Creation Program failed")
        print("\n")
        time.sleep(5)

    def call_inbound_delivery_program(self):
        if not self._run_script("2_Pre_Allocate_IBD.py", "Pre Allocate Inbound Delivery Program"):
            raise RuntimeError("Pre Allocate Inbound Delivery Program failed")
        print("\n")
        time.sleep(5)

    def call_appointment_program(self):
        if not self._run_script("98_Dock_Door_Check.py", "Dock Door Check Program"):
            raise RuntimeError("Dock Door Check Program failed")
        if not self._run_script("3_Schedule_Appointment.py", "Schedule Appointment Program"):
            raise RuntimeError("Schedule Appointment Program failed")
        if not self._run_script("4_Check_In.py", "Check-In Program"):
            raise RuntimeError("Check-In Program failed")
        print("\n")
        time.sleep(5)

    def call_rf_receiving_program(self):
        if not self._run_script("5_RF_Receiving.py", "RF Receiving Program"):
            raise RuntimeError("RF Receiving Program failed")
        print("\n")
        time.sleep(5)

    def call_drop_location_program(self):
        if not self._run_script("6_RF_Locate_Pallet.py", "RF Locate Pallet Program"):
            raise RuntimeError("RF Locate Pallet Program failed")
        print("\n")
        time.sleep(5)

    def call_putaway_complete_program(self):
        if not self._run_script("7_RF_Putaway_Carton_Storage.py", "RF Putaway Carton Storage Program"):
            raise RuntimeError("RF Putaway Carton Storage Program failed")
        print("\n")
        time.sleep(5)

    def call_asn_verify_program(self):
        if not self._run_script("8_ASN_Verify.py", "ASN Verify, Check Out and Release Dock Door Program"):
            raise RuntimeError("ASN Verify, Check Out and Release Dock Door Program failed")
        print("\n")
        time.sleep(5)

    # def call_exception_flow(self):
    #     logging.info("Exception Flow Started")
    #     logging.info("Filling iLPN Information for Routing Task Completed")
    #     self.iLPN_information.search_lpn_information()
    #     logging.info("Completed iLPN Information filling")
    #     logging.info("Starting Routing Task Complete Flow")
    #     self.routing_task_completed.create_routing_task_complete()
    #     logging.info("Routing Task Complete Flow Completed")
    #     logging.info("Exception Flow Completed")

    def get_inbound_master_worksheet_extract(self):
        """Orchestrates the inbound process based on flags from a worksheet."""
        worksheet_entries = self.worksheet_extractor.extract_master_sheet_from_worksheet()

        if not worksheet_entries:
            logging.error("The worksheet returned no entries. Check the worksheet extraction program.")
            return

        # Define the sequence of operations, their flags, and associated logic
        operations = [
            {'flag': 'CreateASN', 'method': self.call_asn_creation_program},
            {'flag': 'InboundDelivery', 'method': self.call_inbound_delivery_program},
            {'flag': 'Appointment', 'method': self.call_appointment_program},
            {'flag': 'Receiving', 'method': self.call_rf_receiving_program},
            {'flag': 'DropLocation', 'method': self.call_drop_location_program},
            {'flag': 'PutawayComplete', 'method': self.call_putaway_complete_program},
            {'flag': 'ASNVerify', 'method': self.call_asn_verify_program},
            # Future AU steps can be added here in sequence:
        ]

        for entry in worksheet_entries:
            run_started_at = datetime.now()
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.environ["AU_EXECUTION_RUN_ID"] = run_id
            logging.info(f"Processing entry: {entry}")
            logging.info(f"Execution summary run id: {run_id}")
            execution_status = "SUCCESS"
            failure_reason = ""
            completed_steps = []

            if entry.get("RunAll") == 'Y':
                run_all_operations = operations
                if entry.get("CreateASN") != "Y":
                    logging.info(
                        "RunAll is Y and CreateASN is not Y; skipping ASN Creation and using "
                        "existing ASN values from MasterInput."
                    )
                    run_all_operations = operations[1:]

                for op in run_all_operations:
                    try:
                        op['method']()
                        completed_steps.append(op['flag'])
                    except RuntimeError as ex:
                        logging.error(str(ex))
                        execution_status = "FAILED"
                        failure_reason = str(ex)
                        break
                if execution_status == "SUCCESS":
                    logging.info("Run All Program Completed Successfully")
                run_ended_at = datetime.now()
                summary_path = ExecutionReportWriter().write_end_to_end_summary(
                    run_user=os.getenv("USER", ""),
                    started_at=run_started_at,
                    ended_at=run_ended_at,
                    status=execution_status,
                    selected_flags=entry,
                    completed_steps=completed_steps,
                    error_message=failure_reason,
                )
                logging.info(f"End-to-end execution summary updated: {summary_path}")
                if execution_status == "FAILED":
                    return
                continue

            # Find the first operation flagged with 'Y'
            start_index = -1
            for i, op in enumerate(operations):
                if entry.get(op['flag']) == 'Y':
                    start_index = i
                    break

            if start_index == -1:
                logging.info("No operation flags set to 'Y'. No output produced for this entry.")
                run_ended_at = datetime.now()
                summary_path = ExecutionReportWriter().write_end_to_end_summary(
                    run_user=os.getenv("USER", ""),
                    started_at=run_started_at,
                    ended_at=run_ended_at,
                    status="SKIPPED",
                    selected_flags=entry,
                    completed_steps=[],
                    error_message="No operation flags were set to Y.",
                )
                logging.info(f"End-to-end execution summary updated: {summary_path}")
                continue

            # Execute all operations from the starting point that are flagged with 'Y'
            methods_to_run = []

            for i in range(start_index, len(operations)):
                op = operations[i]
                # This logic runs a contiguous block of 'Y's from the starting point
                if entry.get(op['flag']) == 'Y':
                    methods_to_run.append(op['method'])
                else:
                    break  # Stop at the first non-'Y' flag

            if methods_to_run:
                if (
                    entry.get("CreateASN") != "Y"
                    and entry.get("InboundDelivery") != "Y"
                    and (entry.get("Appointment") == "Y" or entry.get("Receiving") == "Y")
                ):
                    logging.info(
                        "CreateASN and InboundDelivery flags are not Y; proceeding with "
                        "Appointment/Receiving using existing MasterInput InboundDelivery values."
                    )
                if (
                    (entry.get("DropLocation") == "Y" or entry.get("PutawayComplete") == "Y")
                    and entry.get("Receiving") != "Y"
                ):
                    logging.info(
                        "DropLocation/PutawayComplete triggered without Receiving; using existing "
                        "MasterInput PalletId values."
                    )
                if (
                    entry.get("ASNVerify") == "Y"
                    and entry.get("CreateASN") != "Y"
                    and entry.get("InboundDelivery") != "Y"
                    and entry.get("Appointment") != "Y"
                    and entry.get("Receiving") != "Y"
                    and entry.get("DropLocation") != "Y"
                    and entry.get("PutawayComplete") != "Y"
                ):
                    logging.info(
                        "ASNVerify-only run detected; using existing MasterInput ASNID values."
                    )
                for index, method in enumerate(methods_to_run):
                    try:
                        method()
                        completed_steps.append(operations[start_index + index]["flag"])
                    except RuntimeError as ex:
                        logging.error(str(ex))
                        execution_status = "FAILED"
                        failure_reason = str(ex)
                        break

                if execution_status == "SUCCESS":
                    logging.info("Program Completed Successfully")
            else:
                # This case should not be reached due to the start_index check, but is here for safety
                logging.info("The combination provided doesn't match the requirement.")
                execution_status = "SKIPPED"
                failure_reason = "The combination provided does not match execution requirements."

            run_ended_at = datetime.now()
            summary_path = ExecutionReportWriter().write_end_to_end_summary(
                run_user=os.getenv("USER", ""),
                started_at=run_started_at,
                ended_at=run_ended_at,
                status=execution_status,
                selected_flags=entry,
                completed_steps=completed_steps,
                error_message=failure_reason,
            )
            logging.info(f"End-to-end execution summary updated: {summary_path}")
            if execution_status == "FAILED":
                return

if __name__ == "__main__":
    inbound_master = inbound_master_step()
    inbound_master.get_inbound_master_worksheet_extract()