import argparse
from datetime import datetime
import logging
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests

# Ensure project root is importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Inbound.ASN_Creation import ASN_Creation
from Inbound.Inbound_payload_generation.ASN_Creation_Payload import Asn_Payload_Generator


def _configure_console_logging():
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(threadName)s - %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)


def _enable_file_logging(log_file):
    log_path = Path(log_file).expanduser().resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(threadName)s - %(message)s")
    )

    logging.getLogger().addHandler(file_handler)
    logging.info(f"Execution log file: {log_path}")


def _build_run_log_path(log_file_arg):
    run_suffix = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    if log_file_arg:
        base_path = Path(log_file_arg).expanduser()
        suffix = base_path.suffix or ".log"
        stem = base_path.stem if base_path.suffix else base_path.name
        return base_path.with_name(f"{stem}_{run_suffix}{suffix}")

    return Path(__file__).resolve().parent / "logs" / f"ASN_Creation_Multithread_{run_suffix}.log"


class ASN_Creation_Multithread(ASN_Creation):
    def __init__(self, max_workers=5, request_timeout=30):
        self.max_workers = max(1, int(max_workers))
        self.request_timeout = max(1, int(request_timeout))

    @staticmethod
    def _group_payloads_by_env(payload_packages):
        payloads_by_env = defaultdict(list)
        for package in payload_packages:
            env = package.get("environment")
            payload = package.get("payload")
            if env and payload:
                payloads_by_env[env].append(payload)
            else:
                logging.error(f"WARNING: Skipping malformed package: {package}")
        return payloads_by_env

    @staticmethod
    def _build_headers(plant_id, bearer_token):
        return {
            "content-type": "application/json",
            "organization": str(plant_id),
            "location": str(plant_id),
            "authorization": "Bearer " + bearer_token,
        }

    @staticmethod
    def _build_success_rows(environment, plant_id, payload_to_send):
        asn_id = payload_to_send.get("AsnId")
        origin_facility = payload_to_send.get("OriginFacilityId")
        lpn_list = payload_to_send.get("Lpn", [])
        carrier_id = payload_to_send.get("CarrierId")

        report_entries = []
        for lpn in lpn_list:
            lpn_id = lpn.get("LpnId")
            lpn_detail = lpn.get("LpnDetail") or []
            if lpn_detail:
                item_id = lpn_detail[0].get("ItemId")
                quantity = lpn_detail[0].get("ShippedQuantity")
                report_entries.append(
                    {
                        "PLANT": plant_id,
                        "ENVN": environment,
                        "ASN_ID": asn_id,
                        "LPN_ID": lpn_id,
                        "ITEM_ID": item_id,
                        "QTY": quantity,
                        "O_FACILITY": origin_facility,
                        "CARRIER": carrier_id,
                    }
                )

        current_lpns = [lpn.get("LpnId") for lpn in lpn_list if lpn.get("LpnId")]
        output_row = {
            "PLANT": plant_id,
            "ENVN": environment,
            "ASN_ID": asn_id,
            "LPN_ID": ";".join(current_lpns),
            "Pre_Allocate": "Y",
            "Failed": "N",
        }
        return report_entries, output_row

    def _send_single_payload(self, environment, index, total_payloads, payload_to_send, bearer_token, verify):
        try:
            plant_id = payload_to_send["OrgId"]
            logging.info(
                f"[{environment.upper()}] Processing Payload {index}/{total_payloads} for Plant {plant_id}"
            )

            env_handler = AWM_Env()
            env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
            url_value = env_handler.get_program_url(program=Path(__file__).stem.replace("_Multithread", ""))
            headers = self._build_headers(plant_id, bearer_token)

            response = requests.post(
                url=url_value,
                headers=headers,
                json=payload_to_send,
                verify=verify,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            logging.info(
                f"[{environment.upper()}] Payload {index}/{total_payloads} sent successfully. "
                f"Success: {response_data.get('success', 'N/A')}"
            )

            report_entries, output_row = self._build_success_rows(environment, plant_id, payload_to_send)
            return True, report_entries, output_row
        except KeyError as exc:
            logging.error(f"ERROR: Could not process payload {index}. Data is malformed. Missing key: {exc}")
        except requests.exceptions.RequestException as exc:
            logging.error(f"ERROR: API request failed for payload {index}: {exc}")
            if exc.response is not None:
                logging.error(f"Status Code: {exc.response.status_code}, Response: {exc.response.text}")
        except Exception as exc:
            logging.error(f"ERROR: An unexpected error occurred for payload {index}: {exc}")
        return False, [], None

    @staticmethod
    def _write_asn_creation_report(extracted_report_data):
        if not extracted_report_data:
            logging.info("No data was successfully processed to generate a report.")
            return

        logging.info("Generating Report")
        try:
            report_df = pd.DataFrame(extracted_report_data)
            output_dir = Path("../Output_files")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filepath = output_dir / "ASN_Creation_Report.xlsx"
            report_df.to_excel(output_filepath, index=False)
            logging.info(f"Successfully created report: {output_filepath}")
        except Exception as exc:
            logging.error(f"Failed to create Excel report. Error: {exc}")

    @staticmethod
    def _write_worksheet_output(output_data):
        if not output_data:
            logging.info("No data was successfully processed to generate an input sheet.")
            return

        logging.info("Generating input sheet from the create ASN output")
        try:
            report_df = pd.DataFrame(output_data)
            output_dir = Path("../Input_files")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filepath = output_dir / "WorkSheet.xlsx"

            with pd.ExcelWriter(output_filepath, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
                asn_df = report_df.rename(
                    columns={
                        "PLANT": "Plant",
                        "ENVN": "Environment",
                        "ASN_ID": "ASNID",
                        "LPN_ID": "LPNID",
                        "Pre_Allocate": "Pre_Allocate",
                        "Failed": "Failed",
                    }
                )
                asn_df.to_excel(writer, sheet_name="MasterInput", index=False)

            logging.info(f"Successfully created multi-sheet report: {output_filepath}")
        except Exception as exc:
            logging.error(f"ERROR: Failed to create multi-sheet Excel report. Error: {exc}")

    def create_asns(self):
        asn_gen = Asn_Payload_Generator()
        payload_packages = asn_gen.generate_payloads
        if not payload_packages:
            logging.error("No payloads were generated. Please check your Excel input and generator logic.")
            return

        payloads_by_env = self._group_payloads_by_env(payload_packages)
        verify = self._get_ssl_verify_config()

        extracted_report_data = []
        output_data = []

        for environment, payloads in payloads_by_env.items():
            logging.info(f"Processing {len(payloads)} Payloads for Environment: {environment.upper()}")
            if not payloads:
                logging.error(f"WARNING: Skipping empty payload list for environment {environment.upper()}.")
                continue

            try:
                plant_id_for_token = payloads[0].get("OrgId")
                if not plant_id_for_token:
                    logging.error(
                        f"FATAL ERROR: Cannot get token. payload for {environment.upper()} is missing 'OrgId'"
                    )
                    continue

                token_handler = Get_Token(env=environment.lower(), plant=plant_id_for_token)
                bearer_token = token_handler.get_bearer()
                logging.info(f"Successfully retrieved token for {environment.upper()} environment.")
            except Exception as exc:
                logging.error(f"FATAL ERROR: Could not process batch for environment {environment.upper()}. Error: {exc}")
                continue

            total_payloads = len(payloads)
            worker_count = min(self.max_workers, total_payloads)
            logging.info(f"[{environment.upper()}] Using {worker_count} worker thread(s).")

            success_count = 0
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = [
                    executor.submit(
                        self._send_single_payload,
                        environment,
                        index,
                        total_payloads,
                        payload_to_send,
                        bearer_token,
                        verify,
                    )
                    for index, payload_to_send in enumerate(payloads, start=1)
                ]

                for future in as_completed(futures):
                    success, report_entries, output_row = future.result()
                    if success:
                        success_count += 1
                        extracted_report_data.extend(report_entries)
                        if output_row:
                            output_data.append(output_row)

            failed_count = total_payloads - success_count
            logging.info(
                f"[{environment.upper()}] Completed ASN creation. "
                f"Success: {success_count}, Failed: {failed_count}, Total: {total_payloads}"
            )

        self._write_asn_creation_report(extracted_report_data)
        self._write_worksheet_output(output_data)


def _prompt_worker_count(default_workers=5):
    raw_value = input(f"Enter number of worker threads (default {default_workers}): ").strip()
    if not raw_value:
        return default_workers

    try:
        parsed = int(raw_value)
        if parsed < 1:
            raise ValueError
        return parsed
    except ValueError:
        logging.warning(f"Invalid worker count '{raw_value}'. Falling back to default {default_workers}.")
        return default_workers


def _parse_args():
    parser = argparse.ArgumentParser(description="Run ASN creation in multithreaded mode.")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of concurrent worker threads. If omitted, you will be prompted.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP request timeout in seconds for each payload (default: 30).",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Base log file path. A unique timestamped file is created for each run.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    _configure_console_logging()
    run_log_path = _build_run_log_path(args.log_file)
    _enable_file_logging(str(run_log_path))
    workers = args.workers

    if workers is None:
        try:
            workers = _prompt_worker_count(default_workers=5)
        except EOFError:
            workers = 5
            logging.info("No interactive input available. Using default workers=5.")

    asn_create = ASN_Creation_Multithread(max_workers=workers, request_timeout=args.timeout)
    asn_create.create_asns()

# How to run
# Prompt for workers:
# python3 "Inbound/ASN_Creation_Multithread.py"
# Set workers directly:
# python3 "Inbound/ASN_Creation_Multithread.py" --workers 10
# Set timeout too:
# python3 "Inbound/ASN_Creation_Multithread.py" --workers 10 --timeout 45
# Specify log file base path (still one unique file per run):
# python3 "Inbound/ASN_Creation_Multithread.py" --workers 10 --log-file "Inbound/logs/asn_run.log"