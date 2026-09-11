import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
from pathlib import Path
import sys
import threading

import requests

# Ensure Australia_Impact root is on sys.path for local package imports.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # .../Australia_Impact
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
FFR_NUMBER_STORE_FILE = PROJECT_ROOT / "Output_files" / "latest_created_ffr_numbers.txt"

from Environment.FR_Preprocessor_Environment import FR_Preprocessor_Env
from Outbound.Outbound_Payload_Generation.FR_Creation_Payload import FR_Order_Creation_Payload


def _configure_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(console_handler)


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
    return CURRENT_DIR / "logs" / f"FR_Order_Creation_{run_suffix}.log"


class FROrderCreationRunner:
    def __init__(self, max_workers=5, dry_run=False):
        self.max_workers = min(10, max(1, int(max_workers)))
        self.dry_run = dry_run
        self.fr_generation = FR_Order_Creation_Payload()
        self.final_payloads = self.fr_generation.generate_payloads
        self.worksheet = self.fr_generation.worksheet
        self.access_token_by_env = {}
        self._token_lock = threading.Lock()
        self.env_sequence = self._build_env_sequence_from_input()

    @staticmethod
    def _normalize_env_name(environment):
        env = str(environment).strip().upper() if environment is not None else ""
        return env if env else "QA"

    def _build_env_sequence_from_input(self):
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

    def _get_env_for_payload_index(self, index):
        if index < len(self.env_sequence):
            return self.env_sequence[index]
        if self.env_sequence:
            return self.env_sequence[-1]
        return "QA"

    def _get_access_token(self, env_name):
        env_name = self._normalize_env_name(env_name)
        if env_name in self.access_token_by_env:
            return self.access_token_by_env[env_name]

        with self._token_lock:
            if env_name in self.access_token_by_env:
                return self.access_token_by_env[env_name]

            env_config = FR_Preprocessor_Env(environment=env_name)
            token_response = requests.post(
                url=env_config.token_url,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=env_config.get_token_payload(),
                timeout=30,
            )
            token_response.raise_for_status()
            raw_token = token_response.json().get("access_token")
            if not raw_token:
                raise ValueError(f"Token API response did not contain access_token for env {env_name}.")

            bearer_token = f"Bearer {raw_token}"
            self.access_token_by_env[env_name] = bearer_token
            return bearer_token

    @staticmethod
    def _sanitize_for_json(value):
        if isinstance(value, dict):
            return {key: FROrderCreationRunner._sanitize_for_json(val) for key, val in value.items()}
        if isinstance(value, list):
            return [FROrderCreationRunner._sanitize_for_json(item) for item in value]
        if isinstance(value, tuple):
            return tuple(FROrderCreationRunner._sanitize_for_json(item) for item in value)
        return value

    @staticmethod
    def _extract_order_number(payload):
        return (
            payload.get("fulfillmentRequestHeader", {}).get("fulfillmentRequestNumber")
            if isinstance(payload, dict)
            else None
        )

    def _persist_created_ffr_numbers(self):
        """
        Store created FFR numbers as comma-separated values.
        Overwrites on every run so old values are cleared automatically.
        """
        ffr_numbers = []
        for payload in self.final_payloads:
            ffr_number = self._extract_order_number(payload)
            if ffr_number:
                ffr_numbers.append(str(ffr_number))

        FFR_NUMBER_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
        FFR_NUMBER_STORE_FILE.write_text(",".join(ffr_numbers), encoding="utf-8")
        logging.info(f"Stored {len(ffr_numbers)} FFR number(s) in {FFR_NUMBER_STORE_FILE}")

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
            headers = {"Authorization": bearer_token, "Content-Type": env_config.content_type}
            response = requests.post(
                url=env_config.request_url,
                headers=headers,
                json=self._sanitize_for_json(payload_to_send),
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

    def _send_payload_batch(self, indexed_payloads, total_payloads):
        if not indexed_payloads:
            return 0, 0

        worker_count = self._resolve_worker_count(total_payloads, len(indexed_payloads))
        success_count = 0
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(self._send_single_payload, index, payload_to_send, total_payloads)
                for index, payload_to_send in indexed_payloads
            ]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1

        failed_count = len(indexed_payloads) - success_count
        return success_count, failed_count

    def _resolve_worker_count(self, total_payloads, batch_size):
        """
        Worker policy:
        - <= 5 orders: 1 worker
        - 6 to 100 orders: 5 workers
        - > 100 orders: 10 workers
        Hard-capped at 10 and never exceeds current batch size.
        """
        if total_payloads <= 5:
            target_workers = 1
        elif total_payloads <= 100:
            target_workers = 5
        else:
            target_workers = 10

        target_workers = min(target_workers, 10, self.max_workers)
        return max(1, min(batch_size, target_workers))

    def create_orders(self, test_first_then_bulk=False):
        # Always refresh stored FFR list for this run.
        self._persist_created_ffr_numbers()

        if not self.final_payloads:
            logging.error("No FR payloads were generated. Please check your FR payload generator input.")
            return

        total_payloads = len(self.final_payloads)
        worker_count = self._resolve_worker_count(total_payloads, total_payloads)
        logging.info(f"Input workbook: {self.worksheet.excel_file_path}")
        logging.info(f"Total payloads to send: {total_payloads}")
        logging.info(f"Using {worker_count} worker thread(s).")
        if self.dry_run:
            logging.info("Dry-run mode enabled: no API requests will be executed.")

        if not test_first_then_bulk or total_payloads == 1:
            indexed_payloads = list(enumerate(self.final_payloads, start=1))
            success_count, failed_count = self._send_payload_batch(indexed_payloads, total_payloads)
            logging.info(
                f"Completed order creation. Success: {success_count}, Failed: {failed_count}, Total: {total_payloads}"
            )
            return

        logging.info("Test-first-then-bulk enabled: sending first payload before remaining batch.")
        first_success = self._send_single_payload(1, self.final_payloads[0], total_payloads)
        if not first_success:
            logging.error(
                f"First payload validation failed. Aborting remaining {total_payloads - 1} payload(s)."
            )
            logging.info(
                f"Completed order creation. Success: 0, Failed: 1, Skipped: {total_payloads - 1}, Total: {total_payloads}"
            )
            return

        indexed_remaining = list(enumerate(self.final_payloads[1:], start=2))
        success_remaining, failed_remaining = self._send_payload_batch(indexed_remaining, total_payloads)
        success_count = 1 + success_remaining
        failed_count = failed_remaining
        logging.info(
            f"Completed order creation. Success: {success_count}, Failed: {failed_count}, Total: {total_payloads}"
        )


def _parse_args():
    parser = argparse.ArgumentParser(description="Australia Impact FR order creation.")
    parser.add_argument("--workers", type=int, default=5, help="Concurrent worker threads (default: 5).")
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
    parser.add_argument(
        "--test-first-then-bulk",
        action="store_true",
        help="Send first payload as validation, then send remaining payloads only if first succeeds.",
    )
    return parser.parse_args()


def main():
    _configure_logging()
    args = _parse_args()
    _enable_file_logging(str(_build_run_log_path(args.log_file)))
    FROrderCreationRunner(max_workers=args.workers, dry_run=args.dry_run).create_orders(
        test_first_then_bulk=args.test_first_then_bulk
    )


if __name__ == "__main__":
    main()
