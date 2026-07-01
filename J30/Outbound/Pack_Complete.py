import json
import requests
import logging
import sys
import time
import os
from pathlib import Path

# Ensure project root is importable when running this file directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.Pack_Complete_Payload import Pack_Complete_Payload
from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Pack_Complete:

    def __init__(self):
        self.pack_complete_payload = Pack_Complete_Payload().pack_complete_payload()

    @staticmethod
    def _get_ssl_verify_config():
        disable_ssl_verify = os.getenv("NIKE_DISABLE_SSL_VERIFY", "").strip().lower() in {"1", "true", "yes", "y"}
        ca_bundle = os.getenv("NIKE_CA_BUNDLE", "").strip() or os.getenv("REQUESTS_CA_BUNDLE", "").strip()
        return False if disable_ssl_verify else (ca_bundle if ca_bundle else True)

    def send_pack_complete_payload(self):
        if not self.pack_complete_payload:
            logging.error("No payload were generated in Pack Complete Payload program")
            return

        plant = self.pack_complete_payload['Plant']
        envn = self.pack_complete_payload['Env']
        payloads = self.pack_complete_payload['Payloads']

        if not plant and envn and payloads:
            logging.error(f"INFO: Skipping row as 'Plant' or 'Environment' or 'Payload' is missing")

        logging.info(f"Processing {len(payloads)} Payloads for Environment: {envn.upper()}")
        verify = self._get_ssl_verify_config()

        try:
            plant_id_for_token = plant
            token_handler = Get_Token(env=envn.lower(), plant=str(plant_id_for_token))
            bearer_token = token_handler.get_bearer()
            logging.info(f"Successfully retrieved token for {envn.upper()} environment.")

            env_handler = AWM_OB_Env()
            env_handler.get_wm_host(host=envn.lower(), facility=str(plant_id_for_token))
            url_value = env_handler.get_program_url(program='PackComplete')
            print(f"Sending payload to URL: {url_value}")

            for i, payload_to_send in enumerate(payloads):
                try:
                    print(
                        f"[{envn.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id_for_token}")

                    header = {
                        "content-type": "application/json",
                        "organization": str(plant_id_for_token),
                        "location": str(plant_id_for_token),
                        "authorization": 'Bearer ' + bearer_token
                    }

                    response = requests.post(url=url_value, json=payload_to_send, headers=header, verify=verify)
                    response.raise_for_status()

                except KeyError as e:
                    logging.error(f"ERROR: Could not process payload {i + 1}. Data is malformed. Missing key: {e}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                    if e.response is not None:
                        logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
                except Exception as e:
                    logging.error(f"ERROR: An unexpected error occurred for payload {i + 1}: {e}")

        except Exception as e:
            logging.error(f"FATAL ERROR: Could not process batch for environment {envn.upper()}. Error: {e}")


# def run_pack_complete_every(interval_seconds=20):
#     logging.info(
#         f"Starting Pack Complete scheduler. Running every {interval_seconds} seconds. Press Ctrl+C to stop."
#     )
#     try:
#         while True:
#             logging.info("Starting Pack Complete run...")
#             Pack_Complete().send_pack_complete_payload()
#             logging.info(f"Run complete. Waiting {interval_seconds} seconds for next run...")
#             time.sleep(interval_seconds)
#     except KeyboardInterrupt:
#         logging.info("Hard stop received (Ctrl+C). Pack Complete scheduler stopped.")


if __name__ == '__main__':
    # run_pack_complete_every(interval_seconds=20)
    initiate = Pack_Complete()
    initiate.send_pack_complete_payload()


# How to run
# From your project, run:

# python "Outbound/Pack_Complete.py"
# To stop:

# Press Ctrl+C in the terminal