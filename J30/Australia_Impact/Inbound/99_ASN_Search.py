import requests
import json
import logging
from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env
from pathlib import Path
import pandas as pd
from Australia_Impact.Inbound.Inbound_payload_generation.ASN_Search_Payload import ASN_Search_Payload

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
AUSTRALIA_IMPACT_ROOT = SCRIPT_DIR.parent

class ASN_Search:

    def __init__(self):
        # --- Configuration ---
        # Centralize configuration variables for easy changes.
        self.output_dir = AUSTRALIA_IMPACT_ROOT / "Output_files"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_FILENAME = self.output_dir / "ASN_Search_Results.xlsx"


    def search_asn_sending(self):
        """Main function to orchestrate the ASN search process."""
        asn_search_payload_init = ASN_Search_Payload()
        search_tasks = asn_search_payload_init.parse_asn_search_worksheet()
        if not search_tasks:
            logging.info("Script finished: No valid search tasks for ASN search to process.")
            return

        all_results = []  # --- Collect all results here before writing to file ---
        raw_data = None
        response_data = ''
        # --- Loop correctly over each task ---
        # The try/except block is now INSIDE the loop to handle errors per task.
        for i, task in enumerate(search_tasks):
            # --- FIX: Use correct, lowercase dictionary keys ---
            envn = task['environment']
            plant_id = task['plant']
            asn_ids = task['asn_ids']

            logging.info(f"Processing Task {i+1}/{len(search_tasks)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program="ASN_Search")
                if not api_url:
                    logging.error(
                        f"Could not resolve endpoint URL for program ASN_Search in {envn.upper()}/{plant_id}."
                    )
                    continue
                logging.info(f"Target URL: {api_url}")

                # --- 3. Request Headers & Payload ---
                headers = {
                    "Content-Type": "application/json",
                    "organization": plant_id, # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                    "Authorization": f"Bearer {bearer_token}"
                }

                # Creates a string like "('ASN1','ASN2','ASN3')"
                query_values = "','".join(asn_ids)
                # --- Correctly format the 'in' query string ---
                query_string = f"AsnId in ('{query_values}')"

                payload = {"Query": query_string}
                # print(f"Sending Payload: {json.dumps(payload)}")

                # --- 4. API Call ---
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                raw_data = response_data.get("data")

                # --- 5. Process and Collect Response ---
                extracted_data = asn_search_payload_init.parse_asn_response(response_data)
                if extracted_data:
                    logging.info(f"Success: Found {len(extracted_data)} detail rows for this task.")
                    all_results.extend(extracted_data) # Add results to the master list

            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error occurred: {http_err}")
                if http_err.response:
                    logging.error(f"Response content: {http_err.response.text}")
            except requests.exceptions.RequestException as req_err:
                logging.error(f"A request error occurred: {req_err}")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

        # --- 6. Final Export ---
        # This block runs once after all tasks are completed.
        if not all_results:
            logging.info("Script finished, but no results were collected from any API calls")
            return

        logging.info(f"Consolidating and Exporting Results")
        try:
            # Create the main DataFrame with the parsed results
            df_details = pd.DataFrame(all_results)
            # print("--- ASN Details ---")
            # print(df_details.to_string(index=False))

            # Use pd.ExcelWriter to save multiple sheets to the SAME file
            with pd.ExcelWriter(self.OUTPUT_FILENAME, engine='openpyxl') as writer:
                # Write the first sheet
                df_details.to_excel(writer, sheet_name="ASN_Details", index=False)

                if raw_data:
                    for each_payload in raw_data:
                        # Convert the entire raw dictionary to a formatted JSON string
                        raw_json_string = json.dumps(each_payload, indent=4)
                        # Create a simple DataFrame to hold this string
                        df_raw = pd.DataFrame({'Raw_Payload': [raw_json_string]})

                        # Write the second sheet
                        df_raw.to_excel(writer, sheet_name="Raw_ASN_Payload", index=False)
                        logging.info("Raw Payload updated in Excel Sheet: Raw_ASN_Payload")

            logging.info(f"Successfully exported {len(df_details)} total rows to '{self.OUTPUT_FILENAME}'")

        except Exception as e:
            logging.error(f" Error exporting final report to Excel: {e}")

        return response_data


    def search_asn_get_ib_delivery(self):

        asn_search_payload_init = ASN_Search_Payload()
        search_tasks = asn_search_payload_init.parse_asn_inbound_delivery_search_worksheet()
        if not search_tasks:
            logging.info("Script finished: No valid search tasks for ASN search to process.")
            return

        all_results = []  # --- Collect all results here before writing to file ---
        # --- Loop correctly over each task ---
        # The try/except block is now INSIDE the loop to handle errors per task.
        for i, task in enumerate(search_tasks):
            # --- FIX: Use correct, lowercase dictionary keys ---
            envn = task['environment']
            plant_id = task['plant']
            asn_ids = task['asn_ids']

            logging.info(f"Processing Task {i + 1}/{len(search_tasks)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program="ASN_Search")
                if not api_url:
                    logging.error(
                        f"Could not resolve endpoint URL for program ASN_Search in {envn.upper()}/{plant_id}."
                    )
                    continue
                logging.info(f"Target URL: {api_url}")

                # --- 3. Request Headers & Payload ---
                headers = {
                    "Content-Type": "application/json",
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                    "Authorization": f"Bearer {bearer_token}"
                }

                # Creates a string like "('ASN1','ASN2','ASN3')"
                query_values = "','".join(asn_ids)
                # --- Correctly format the 'in' query string ---
                query_string = f"AsnId in ('{query_values}')"

                payload = {"Query": query_string}
                # print(f"Sending Payload: {json.dumps(payload)}")

                # --- 4. API Call ---
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                raw_data = response_data.get("data")

                # --- 5. Process and Collect Response ---
                extracted_data = asn_search_payload_init.parse_asn_inbound_delivery_response(response_data)
                if extracted_data:
                    logging.info(f"Success: Found {len(extracted_data)} detail rows for this task.")
                    return extracted_data

            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error occurred: {http_err}")
                if http_err.response:
                    logging.error(f"Response content: {http_err.response.text}")
            except requests.exceptions.RequestException as req_err:
                logging.error(f"A request error occurred: {req_err}")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asn_search = ASN_Search()
    response_data = asn_search.search_asn_sending()
    print(response_data)