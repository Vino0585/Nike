import logging
import sys
import argparse
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

# Ensure project root is importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.Pack_Complete_Payload import Pack_Complete_Payload
from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env

class Pack_Complete_Multithreaded:
    def __init__(self, max_workers=8, request_timeout=60):
        self.max_workers = max_workers
        self.request_timeout = request_timeout
        self.ssl_verify = self._get_ssl_verify_config()

    @staticmethod
    def _get_ssl_verify_config():
        disable_ssl_verify = os.getenv("NIKE_DISABLE_SSL_VERIFY", "").strip().lower() in {"1", "true", "yes", "y"}
        ca_bundle = os.getenv("NIKE_CA_BUNDLE", "").strip() or os.getenv("REQUESTS_CA_BUNDLE", "").strip()
        return False if disable_ssl_verify else (ca_bundle if ca_bundle else True)

    def _build_headers(self, plant_id_for_token, bearer_token):
        return {
            "content-type": "application/json",
            "organization": str(plant_id_for_token),
            "location": str(plant_id_for_token),
            "authorization": "Bearer " + bearer_token,
        }

    def _send_single_payload(self, index, total, payload_to_send, url_value, headers, envn, plant_id_for_token):
        try:
            logging.info(
                f"[{envn.upper()}] Processing Payload {index}/{total} for Plant {plant_id_for_token}"
            )
            response = requests.post(
                url=url_value,
                json=payload_to_send,
                headers=headers,
                verify=self.ssl_verify,
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            return index, True, None
        except KeyError as e:
            message = f"ERROR: Could not process payload {index}. Data is malformed. Missing key: {e}"
            logging.error(message)
            return index, False, message
        except requests.exceptions.RequestException as e:
            message = f"ERROR: API request failed for payload {index}: {e}"
            logging.error(message)
            if e.response is not None:
                logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
            return index, False, message
        except Exception as e:
            message = f"ERROR: An unexpected error occurred for payload {index}: {e}"
            logging.error(message)
            return index, False, message

    def send_pack_complete_payload(self):
        pack_complete_payload = Pack_Complete_Payload().pack_complete_payload()
        if not pack_complete_payload:
            logging.error("No payload were generated in Pack Complete Payload program")
            return

        plant = pack_complete_payload.get("Plant")
        envn = pack_complete_payload.get("Env")
        payloads = pack_complete_payload.get("Payloads") or []

        if not (plant and envn and payloads):
            logging.error("Skipping run because 'Plant', 'Env', or 'Payloads' is missing/empty")
            return

        logging.info(f"Processing {len(payloads)} payloads for Environment: {envn.upper()}")

        try:
            plant_id_for_token = plant
            token_handler = Get_Token(env=envn.lower(), plant=str(plant_id_for_token))
            bearer_token = token_handler.get_bearer()
            logging.info(f"Successfully retrieved token for {envn.upper()} environment.")

            env_handler = AWM_OB_Env()
            env_handler.get_wm_host(host=envn.lower(), facility=str(plant_id_for_token))
            url_value = env_handler.get_program_url(program="PackComplete")
            logging.info(f"Sending payloads to URL: {url_value}")

            headers = self._build_headers(plant_id_for_token, bearer_token)
            total_payloads = len(payloads)
            workers = min(self.max_workers, total_payloads)
            logging.info(f"Using {workers} worker threads for {total_payloads} payloads.")

            failed = 0
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        self._send_single_payload,
                        idx,
                        total_payloads,
                        payload_to_send,
                        url_value,
                        headers,
                        envn,
                        plant_id_for_token,
                    )
                    for idx, payload_to_send in enumerate(payloads, start=1)
                ]

                for future in as_completed(futures):
                    _, success, _ = future.result()
                    if not success:
                        failed += 1

            logging.info(
                f"Pack Complete run finished. Success: {total_payloads - failed}, Failed: {failed}, Total: {total_payloads}"
            )

        except Exception as e:
            logging.error(f"FATAL ERROR: Could not process batch for environment {envn.upper()}. Error: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send Pack Complete payloads concurrently."
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Maximum number of threads used to send payloads (default: 8).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP request timeout in seconds for each payload (default: 60).",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=str(Path(__file__).resolve().parent / "logs"),
        help="Directory where execution log files are written.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=20,
        help="Wait time between runs in seconds (default: 20). Use 0 for no wait.",
    )
    return parser.parse_args()


def configure_logging(log_dir):
    log_directory = Path(log_dir)
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / f"pack_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    logging.info(f"Execution log file: {log_file}")
    return log_file


def run_until_stopped(runner, interval_seconds):
    logging.info(
        f"Starting continuous mode. The job will rerun every {interval_seconds} seconds. Press Ctrl+C to stop."
    )
    try:
        while True:
            logging.info("Starting Pack Complete run...")
            runner.send_pack_complete_payload()
            logging.info("Pack Complete run finished.")
            if interval_seconds > 0:
                logging.info(f"Waiting {interval_seconds} seconds before next run...")
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logging.info("Stop requested (Ctrl+C). Continuous Pack Complete execution stopped.")


if __name__ == "__main__":
    args = parse_args()
    configure_logging(args.log_dir)
    initiate = Pack_Complete_Multithreaded(
        max_workers=args.max_workers,
        request_timeout=args.timeout,
    )
    run_until_stopped(
        runner=initiate,
        interval_seconds=args.interval_seconds,
    )


# How to run
# python "Outbound/Pack_Complete_Multithreaded.py"
# python "Outbound/Pack_Complete_Multithreaded.py" --max-workers 12
# python "Outbound/Pack_Complete_Multithreaded.py" --timeout 90
# python "Outbound/Pack_Complete_Multithreaded.py" --max-workers 12 --timeout 90
# python "Outbound/Pack_Complete_Multithreaded.py" --log-dir "Outbound/logs"
# python "Outbound/Pack_Complete_Multithreaded.py" --interval-seconds 30
# python "Outbound/Pack_Complete_Multithreaded.py" --max-workers 12 --timeout 30 --interval-seconds 30
# Press Ctrl+C to stop continuous execution.

# Example:

# --timeout 30 → each request gets up to 30 seconds
# --timeout 90 → each request gets up to 90 seconds
# Default is 60 seconds right now.
