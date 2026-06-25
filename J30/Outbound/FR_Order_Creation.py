import logging
import requests
import sys
from pathlib import Path

# Ensure project root is on sys.path so `Outbound` and `Environment` packages can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.FR_Creation_Payload import FR_Order_Creation_Payload
from Environment.FR_Preprocessor_Environment import FR_Preprocessor_Env


def _configure_logging():
    """Force console logging so INFO messages always appear when script runs."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root_logger.addHandler(console_handler)

_configure_logging()

class FR_Order_Creation:
    def __init__(self):
        self.fr_generation = FR_Order_Creation_Payload()
        self.final_payloads = self.fr_generation.generate_payloads
        self.env_config = FR_Preprocessor_Env()
        self.access_token = None

    def _get_access_token(self):
        if self.access_token:
            return self.access_token

        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_response = requests.post(
            url=self.env_config.token_url,
            headers=token_headers,
            data=self.env_config.get_token_payload(),
        )
        token_response.raise_for_status()
        token_json = token_response.json()
        raw_token = token_json.get("access_token")
        if not raw_token:
            raise ValueError("Token API response did not contain 'access_token'.")

        self.access_token = f"Bearer {raw_token}"
        return self.access_token

    def _build_headers(self, bearer_token):
        return {
            "Authorization": bearer_token,
            "Content-Type": self.env_config.content_type,
            # "~messageId": str(uuid.uuid4()),
            # "~messageType": "DELIVERYNOTE",
        }

    @staticmethod
    def _extract_order_number(payload):
        return (
            payload.get("fulfillmentRequestHeader", {}).get("fulfillmentRequestNumber")
            if isinstance(payload, dict)
            else None
        )

    def create_orders(self):
        if not self.final_payloads:
            logging.error("No FR payloads were generated. Please check your FR payload generator input.")
            return

        try:
            bearer_token = self._get_access_token()
            logging.info("Successfully retrieved bearer token for FR preprocessor API.")
        except Exception as exc:
            logging.error(f"Failed to retrieve bearer token. Error: {exc}")
            return

        total_payloads = len(self.final_payloads)
        logging.info(f"Total payloads to send: {total_payloads}")

        for index, payload_to_send in enumerate(self.final_payloads, start=1):
            try:
                order_number = self._extract_order_number(payload_to_send) or "UNKNOWN_ORDER"
                logging.info(
                    f"Sending payload {index}/{total_payloads} | "
                    f"Order Number: {order_number}"
                )
                headers = self._build_headers(bearer_token)
                response = requests.post(
                    url=self.env_config.request_url,
                    headers=headers,
                    json=payload_to_send,
                )
                response.raise_for_status()
                logging.info(
                    f"Payload {index}/{total_payloads} sent successfully. "
                    f"Status Code: {response.status_code}"
                )
            except requests.exceptions.RequestException as exc:
                logging.error(f"API request failed for payload {index}: {exc}")
                if exc.response is not None:
                    logging.error(f"Status Code: {exc.response.status_code}, Response: {exc.response.text}")
            except Exception as exc:
                logging.error(f"Unexpected error for payload {index}: {exc}")


if __name__ == "__main__":
    fr_order_creation = FR_Order_Creation()
    fr_order_creation.create_orders()