import logging
import requests
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
import json

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class lpn_list_from_asn:

    def parse_asn_to_lpn_list(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error("-> Success, but no ASN data was returned in the response.")
            return []

        extracted_lpn_ids = []
        for asn in response_data.get("data", []):
            lpn_in_list = []
            for lpn in asn.get("Lpn", []):
                lpn_in_list.append(lpn.get("LpnId"))
            extracted_lpn_ids.append(lpn_in_list)

        return extracted_lpn_ids

    def create_from_asn_list_of_lpn(self, response_data: list) -> list:
        if not response_data:
            logging.info("\nScript finished: No valid search tasks to process.")
            return

        all_results = []  # --- Collect all results here before writing to file ---
        # --- Loop correctly over each task ---
        for i, task in enumerate(response_data):
            for asn in task['asn_ids']:
                envn = task['environment']
                plant_id = task['plant']
                asn_ids = asn

                logging.info(f"Processing Task {i + 1}/{len(response_data)}: Plant {plant_id} ({envn.upper()})")

                try:
                    # --- 1. Authentication ---
                    token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                    bearer_token = token_handler.get_bearer()
                    logging.info("Successfully retrieved token for getting list of lpn from asn search")

                    # --- 2. URL Setup ---
                    awm_env = AWM_Env()
                    awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                    api_url = awm_env.get_program_url(program='ASN_Search')
                    logging.info(f"Target URL: {api_url}")

                    # --- 3. Request Headers & Payload ---
                    headers = {
                        "Content-Type": "application/json",
                        "organization": plant_id,
                        "location": plant_id,
                        "Authorization": f"Bearer {bearer_token}"
                    }

                    # Creates a string like "('ASN1','ASN2','ASN3')"
                    query_values = asn_ids
                    # --- Correctly format the 'in' query string ---
                    query_string = f"AsnId in ('{query_values}')"

                    payload = {"Query": query_string}
                    logging.info(f"Sending Payload: {json.dumps(payload)}")

                    # --- 4. API Call ---
                    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                    response.raise_for_status()
                    response_data = response.json()

                    # --- 5. Process and Collect Response ---
                    extracted_data = self.parse_asn_to_lpn_list(response_data)
                    if extracted_data:
                        logging.info(f"Success: Found {len(extracted_data)} detail rows for this task.")
                        all_results.extend(extracted_data)  # Add results to the master list

                except requests.exceptions.HTTPError as http_err:
                    logging.error(f"HTTP error occurred: {http_err}")
                    if http_err.response:
                        logging.error(f"Response content: {http_err.response.text}")
                except requests.exceptions.RequestException as req_err:
                    logging.error(f"A request error occurred: {req_err}")
                except Exception as e:
                    logging.error(f"An unexpected error occurred: {e}")

        return all_results