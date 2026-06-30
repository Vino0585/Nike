import argparse
from datetime import datetime
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# Ensure project root is on sys.path so package imports work
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Environment.FR_Preprocessor_Environment import FR_Preprocessor_Env
from Outbound.FR_Order_Creation_Prod import FR_Order_Creation_Prod


def _enable_file_logging(log_file):
    log_path = Path(log_file).expanduser().resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(threadName)s - %(message)s")
    )
    root_logger.addHandler(file_handler)
    logging.info(f"Execution log file: {log_path}")


def _build_run_log_path(log_file_arg):
    run_suffix = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    if log_file_arg:
        base_path = Path(log_file_arg).expanduser()
        suffix = base_path.suffix or ".log"
        stem = base_path.stem if base_path.suffix else base_path.name
        return base_path.with_name(f"{stem}_{run_suffix}{suffix}")

    return CURRENT_DIR / "logs" / f"FR_Order_Creation_Prod_Multithread_{run_suffix}.log"


class FR_Order_Creation_Prod_Multithread(FR_Order_Creation_Prod):
    """
    Multithreaded runner for FR order creation.
    Keeps original payload generation and env mapping behavior.
    """

    def __init__(self, max_workers=5, dry_run=False):
        super().__init__()
        self.max_workers = max(1, int(max_workers))
        self.dry_run = dry_run
        self._token_lock = threading.Lock()

    def _build_env_sequence_from_input(self):
        """
        Build env mapping without generating FR order IDs.
        This prevents advancing .fr_order_sequence_state.json twice.
        """
        try:
            extracted_rows = self.worksheet.create_fr_order_extract_parameters()
        except Exception as exc:
            logging.error(f"Failed to read FR worksheet for environment mapping: {exc}")
            return []

        if not extracted_rows:
            return []

        env_sequence = []
        for data_row in extracted_rows:
            env = self._normalize_env_name(data_row.get("environment"))
            raw_count = data_row.get("number_of_Orders")

            try:
                order_count = int(raw_count)
            except (TypeError, ValueError):
                order_count = 0

            if order_count > 0:
                env_sequence.extend([env] * order_count)

        return env_sequence

    def _get_access_token(self, env_name):
        """
        Thread-safe token fetch/cache.
        """
        env_name = self._normalize_env_name(env_name)
        if env_name in self.access_token_by_env:
            return self.access_token_by_env[env_name]

        with self._token_lock:
            if env_name in self.access_token_by_env:
                return self.access_token_by_env[env_name]
            return super()._get_access_token(env_name)

    def _send_single_payload(self, index, payload_to_send, total_payloads):
        try:
            env_name = self._get_env_for_payload_index(index - 1)
            env_config = FR_Preprocessor_Env(environment=env_name)

            order_number = self._extract_order_number(payload_to_send) or "UNKNOWN_ORDER"
            if self.dry_run:
                logging.info(
                    f"[DRY-RUN][{env_name}] Payload {index}/{total_payloads} would be sent | "
                    f"Order Number: {order_number} | URL: {env_config.request_url}"
                )
                return True

            bearer_token = self._get_access_token(env_name)
            logging.info(
                f"[{env_name}] Sending payload {index}/{total_payloads} | "
                f"Order Number: {order_number}"
            )

            headers = self._build_headers(bearer_token, env_config.content_type)
            sanitized_payload = self._sanitize_for_json(payload_to_send)
            response = requests.post(
                url=env_config.request_url,
                headers=headers,
                json=sanitized_payload,
                timeout=30,
            )
            response.raise_for_status()

            logging.info(
                f"[{env_name}] Payload {index}/{total_payloads} sent successfully. "
                f"Status Code: {response.status_code}"
            )
            return True
        except requests.exceptions.RequestException as exc:
            logging.error(f"API request failed for payload {index}: {exc}")
            if exc.response is not None:
                logging.error(f"Status Code: {exc.response.status_code}, Response: {exc.response.text}")
            return False
        except Exception as exc:
            logging.error(f"Unexpected error for payload {index}: {exc}")
            return False

    def create_orders(self):
        if not self.final_payloads:
            logging.error("No FR payloads were generated. Please check your FR payload generator input.")
            return

        total_payloads = len(self.final_payloads)
        worker_count = min(self.max_workers, total_payloads)
        logging.info(f"Total payloads to send: {total_payloads}")
        logging.info(f"Using {worker_count} worker thread(s).")
        if self.dry_run:
            logging.info("Dry-run mode enabled: no API requests will be executed.")

        success_count = 0
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(self._send_single_payload, index, payload_to_send, total_payloads)
                for index, payload_to_send in enumerate(self.final_payloads, start=1)
            ]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1

        failed_count = total_payloads - success_count
        logging.info(
            f"Completed order creation. Success: {success_count}, Failed: {failed_count}, Total: {total_payloads}"
        )


def _parse_args():
    parser = argparse.ArgumentParser(description="Run FR order creation in multithreaded mode.")
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent worker threads (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and log payload dispatch plan without calling APIs.",
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
    run_log_path = _build_run_log_path(args.log_file)
    _enable_file_logging(str(run_log_path))
    fr_order_creation = FR_Order_Creation_Prod_Multithread(
        max_workers=args.workers,
        dry_run=args.dry_run,
    )
    fr_order_creation.create_orders()

# Run it like:

# python3 Outbound/FR_Order_Creation_Prod_Multithread.py
# python3 Outbound/FR_Order_Creation_Prod_Multithread.py --workers 10
# python3 Outbound/FR_Order_Creation_Prod_Multithread.py --dry-run
# python3 Outbound/FR_Order_Creation_Prod_Multithread.py --workers 10 --dry-run
# python3 Outbound/FR_Order_Creation_Prod_Multithread.py --log-file "Outbound/logs/my_run.log"