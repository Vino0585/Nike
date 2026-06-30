import logging
import math
import requests
import sys
from pathlib import Path

# Ensure project root is on sys.path so `Outbound`, `Inbound`, and `Environment` packages can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.FR_Creation_Payload import FR_Order_Creation_Payload
from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Inbound.Inbound_payload_generation.Number_Generation import NumberGeneration
from Environment.FR_Preprocessor_Environment import FR_Preprocessor_Env


def _configure_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(console_handler)


_configure_logging()


class FR_Order_Creation_Prod:
    """
    Environment-aware FR order creation.
    Uses environment value from FR input sheet rows (e.g., QA/PROD)
    and resolves matching preprocessor client config.
    """

    def __init__(self):
        self.fr_generation = FR_Order_Creation_Payload()
        self.final_payloads = self.fr_generation.generate_payloads
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.access_token_by_env = {}
        self.env_sequence = self._build_env_sequence_from_input()

    @staticmethod
    def _normalize_env_name(environment):
        env = str(environment).strip().upper() if environment is not None else ""
        return env if env else "QA"

    def _build_env_sequence_from_input(self):
        """
        Build environment mapping aligned to generated payload order.
        Sequence repeats row environment for each generated order in that row.
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

    def _get_env_for_payload_index(self, index):
        if index < len(self.env_sequence):
            return self.env_sequence[index]
        if self.env_sequence:
            return self.env_sequence[-1]
        return "QA"

    @staticmethod
    def _sanitize_for_json(value):
        if isinstance(value, dict):
            return {key: FR_Order_Creation_Prod._sanitize_for_json(val) for key, val in value.items()}
        if isinstance(value, list):
            return [FR_Order_Creation_Prod._sanitize_for_json(item) for item in value]
        if isinstance(value, tuple):
            return tuple(FR_Order_Creation_Prod._sanitize_for_json(item) for item in value)
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return value
        try:
            if value != value:
                return None
        except Exception:
            pass
        return value

    @staticmethod
    def _extract_order_number(payload):
        return (
            payload.get("fulfillmentRequestHeader", {}).get("fulfillmentRequestNumber")
            if isinstance(payload, dict)
            else None
        )

    def _get_access_token(self, env_name):
        env_name = self._normalize_env_name(env_name)
        if env_name in self.access_token_by_env:
            return self.access_token_by_env[env_name]

        env_config = FR_Preprocessor_Env(environment=env_name)
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_response = requests.post(
            url=env_config.token_url,
            headers=token_headers,
            data=env_config.get_token_payload(),
            timeout=30,
        )
        token_response.raise_for_status()
        raw_token = token_response.json().get("access_token")
        if not raw_token:
            raise ValueError(f"Token API response did not contain 'access_token' for env {env_name}.")

        bearer_token = f"Bearer {raw_token}"
        self.access_token_by_env[env_name] = bearer_token
        return bearer_token

    @staticmethod
    def _build_headers(bearer_token, content_type):
        return {
            "Authorization": bearer_token,
            "Content-Type": content_type,
        }

    def create_orders(self):
        if not self.final_payloads:
            logging.error("No FR payloads were generated. Please check your FR payload generator input.")
            return

        total_payloads = len(self.final_payloads)
        logging.info(f"Total payloads to send: {total_payloads}")

        for index, payload_to_send in enumerate(self.final_payloads, start=1):
            try:
                env_name = self._get_env_for_payload_index(index - 1)
                env_config = FR_Preprocessor_Env(environment=env_name)
                bearer_token = self._get_access_token(env_name)

                order_number = self._extract_order_number(payload_to_send) or "UNKNOWN_ORDER"
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
            except requests.exceptions.RequestException as exc:
                logging.error(f"API request failed for payload {index}: {exc}")
                if exc.response is not None:
                    logging.error(f"Status Code: {exc.response.status_code}, Response: {exc.response.text}")
            except Exception as exc:
                logging.error(f"Unexpected error for payload {index}: {exc}")


if __name__ == "__main__":
    fr_order_creation = FR_Order_Creation_Prod()
    fr_order_creation.create_orders()
