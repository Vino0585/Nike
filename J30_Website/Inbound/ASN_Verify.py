from Payload_generation.ASN_Verify_Payload import ASN_Verify_Payload
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env

import requests
import logging

# Use the logging module for better, more consistent output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ASN_Verify:

    def send_asn_verify(self):
        init_asn_verify_payload = ASN_Verify_Payload()
        asn_verify_payload = init_asn_verify_payload.create_verify_asn_payload()

        for i, payload in enumerate(asn_verify_payload):
            plant_id = payload.get("Plant")
            environment = payload.get("Environment")
            query = payload.get("Query")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=environment.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                if not bearer_token:
                    logging.error(f"No token found for {environment}/{plant_id}. Skipping.")
                    return

                # --- 2. URL Setup ---
                awm_env = AWM_Env()
                awm_env.get_wm_host(host=environment.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='ASN_Verify')
                logging.info(f"Target URL for {plant_id}: {api_url}")

                # --- 3. Request Headers & Payload ---
                headers = {
                    "Content-Type": "application/json",
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                    "Authorization": f"Bearer {bearer_token}"
                }

                # --- 4. Post the request ---
                response = requests.post(api_url, json=query, headers=headers, timeout=30)
                response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
                response_data = response.json()
                logging.info(f"Successfully added ASN for {plant_id}. Response: {response_data.get('success', 'N/A')}")

            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error occurred for {plant_id}: {http_err}")
                if http_err.response:
                    logging.error(f"Response content: {http_err.response.text}")


# asn_verify = ASN_Verify()
# asn_verify.send_asn_verify()