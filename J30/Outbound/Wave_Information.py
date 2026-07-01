import requests
import logging
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so `Environment` and `Outbound` packages can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env
import pandas as pd
from Outbound.Outbound_Payload_Generation.Wave_Information_Payload import Wave_Information_Payload

# Setup basic logging to provide better feedback than print()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR)

class Wave_Information_Search:

    def __init__(self):
        self.wave_information = Wave_Information_Payload()
        self.ssl_verify = self._get_ssl_verify_config()

    @staticmethod
    def _get_ssl_verify_config():
        disable_ssl_verify = os.getenv("NIKE_DISABLE_SSL_VERIFY", "").strip().lower() in {"1", "true", "yes", "y"}
        ca_bundle = os.getenv("NIKE_CA_BUNDLE", "").strip() or os.getenv("REQUESTS_CA_BUNDLE", "").strip()
        return False if disable_ssl_verify else (ca_bundle if ca_bundle else True)

    def search_olpn_payload(self):
        olpn_search_payload = self.wave_information.extract_wave_olpn_information()

        if not olpn_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        all_olpn_results = []

        for i, payload in enumerate(olpn_search_payload):
            envn = payload['Environment']
            plant_id = str(payload['Plant'])
            olpn_payload = payload['Payload']

            logging.info(f"Processing Task {i+1}/{len(olpn_search_payload)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_OB_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='oLPNSearch')
                logging.info(f"Sending payload to URL: {api_url}")

                # --- 3. Request Headers ---
                headers = {
                    'Authorization': f'Bearer {bearer_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                }

                # --- 4. Make API Request Call ---
                response = requests.post(api_url, headers=headers, json=olpn_payload, verify=self.ssl_verify)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                logging.info(f"Successfully received response for Plant {plant_id} ({envn.upper()})")
                raw_data = response.json()

                # --- 5. Process and Collect Response ---
                extracted_data = self.wave_information.parse_wave_olpn_information(raw_data)
                if extracted_data:
                    logging.info(f"Success: Found {len(extracted_data)} detail rows for this task.")
                    all_olpn_results.extend(extracted_data)
                else:
                    logging.info(f"No detail rows found for this task.")

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for Plant {plant_id} ({envn.upper()}): {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for Plant {plant_id} ({envn.upper()}): {e}")

        # --- 6. Final Export ---
        # This block runs once after all tasks are completed.
        if all_olpn_results:
            logging.info("Generating Parent Order Data information in Output_Worksheet excel file")

            try:
                lpn_search_df = pd.DataFrame(all_olpn_results)
                output_dir = Path("../Output_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "oLPN_Search_Result.xlsx"
                if not lpn_search_df.empty:
                    if 'OlpnId' in lpn_search_df.columns:
                        order_search_df = lpn_search_df.sort_values(by=['OlpnId'])
                if not lpn_search_df.empty:
                    # Adjust display options for better alignment
                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.width', 1000)
                    pd.set_option('display.colheader_justify', 'left')
                    print(lpn_search_df.to_string(index=False))
                with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
                    lpn_search_df.to_excel(writer, sheet_name='oLPN_Number', index=False)
                    logging.info(f"Successfully exported Original order to Excel file: {output_filepath}")

            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

        else:
            logging.info("No parent order data available therefore didn't export any data")
            return None


    def search_task_payload(self):
        task_detail_search_payload = self.wave_information.extract_wave_task_detail_information()

        if not task_detail_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        all_task_results = []

        for i, payload in enumerate(task_detail_search_payload):
            envn = payload['Environment']
            plant_id = str(payload['Plant'])
            task_payload = payload['Payload']

            logging.info(f"Processing Task {i + 1}/{len(task_detail_search_payload)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_OB_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='Search_Task_Detail')
                logging.info(f"Sending payload to URL: {api_url}")

                # --- 3. Request Headers ---
                headers = {
                    'Authorization': f'Bearer {bearer_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                }

                # --- 4. Make API Request Call ---
                response = requests.post(api_url, headers=headers, json=task_payload, verify=self.ssl_verify)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                logging.info(f"Successfully received response for Plant {plant_id} ({envn.upper()})")
                raw_data = response.json()

                # --- 5. Process and Collect Response ---
                extracted_data = task_payload.parse_wave_olpn_information(raw_data)
                if extracted_data:
                    logging.info(f"Success: Found {len(extracted_data)} detail rows for this task.")
                    all_task_results.extend(extracted_data)
                else:
                    logging.info(f"No detail rows found for this task.")

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for Plant {plant_id} ({envn.upper()}): {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for Plant {plant_id} ({envn.upper()}): {e}")

        # --- 6. Final Export ---
        # This block runs once after all tasks are completed.
        if all_task_results:
            logging.info("Generating Parent Order Data information in Output_Worksheet excel file")

            try:
                task_search_df = pd.DataFrame(all_task_results)
                output_dir = Path("../Output_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "Task_Search_Result.xlsx"
                if not task_search_df.empty:
                    if 'OlpnId' in task_search_df.columns:
                        order_search_df = task_search_df.sort_values(by=['OlpnId'])
                if not task_search_df.empty:
                    # Adjust display options for better alignment
                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.width', 1000)
                    pd.set_option('display.colheader_justify', 'left')
                    print(task_search_df.to_string(index=False))
                with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
                    task_search_df.to_excel(writer, sheet_name='oLPN_Number', index=False)
                    logging.info(f"Successfully exported Original order to Excel file: {output_filepath}")

            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

        else:
            logging.info("No parent order data available therefore didn't export any data")
            return None


    def search_olpn_info_for_tran_log(self):
        olpn_search_payload = self.wave_information.extract_wave_olpn_information()

        if not olpn_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        all_olpn_results = []

        for i, payload in enumerate(olpn_search_payload):
            envn = payload['Environment']
            plant_id = str(payload['Plant'])
            olpn_payload = payload['Payload']

            logging.info(f"Processing Task {i + 1}/{len(olpn_search_payload)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_OB_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='oLPNSearch')
                logging.info(f"Sending payload to URL: {api_url}")

                # --- 3. Request Headers ---
                headers = {
                    'Authorization': f'Bearer {bearer_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                }

                # --- 4. Make API Request Call ---
                response = requests.post(api_url, headers=headers, json=olpn_payload, verify=self.ssl_verify)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                logging.info(f"Successfully received response for Plant {plant_id} ({envn.upper()})")
                raw_data = response.json()

                # --- 5. Process and Collect Response ---
                extracted_data = self.wave_information.parse_wave_olpn_information_for_tran_log(raw_data)
                if extracted_data:
                    logging.info(f"Success: Found {len(extracted_data)} detail rows for this task.")
                    all_olpn_results.extend(extracted_data)
                else:
                    logging.info(f"No detail rows found for this task.")

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for Plant {plant_id} ({envn.upper()}): {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for Plant {plant_id} ({envn.upper()}): {e}")

        return all_olpn_results

    def search_olpn_payload_for_pack_complete(self):
        olpn_search_payload = self.wave_information.extract_wave_olpn_information_for_pack_message()

        if not olpn_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        oLPN_detail = []

        for i, payload in enumerate(olpn_search_payload):
            envn = payload['Environment']
            plant_id = str(payload['Plant'])
            olpn_payload = payload['Payload']

            logging.info(f"Processing Task {i+1}/{len(olpn_search_payload)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_OB_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='oLPNSearch')
                logging.info(f"Sending payload to URL: {api_url}")

                # --- 3. Request Headers ---
                headers = {
                    'Authorization': f'Bearer {bearer_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                }

                # --- 4. Make API Request Call ---
                response = requests.post(api_url, headers=headers, json=olpn_payload, verify=self.ssl_verify)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                logging.info(f"Successfully received response for Plant {plant_id} ({envn.upper()})")
                raw_data = response.json()
                response_data = raw_data.get('data', [])
                if response_data:
                    for data_entry in response_data:
                        olpn_detail_rows = data_entry.get('OlpnDetail', [])
                        if olpn_detail_rows:
                            oLPN_detail.extend(olpn_detail_rows)

                logging.info(f"Success: Found {len(response_data)} oLPN row(s) for this task.")

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for Plant {plant_id} ({envn.upper()}): {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for Plant {plant_id} ({envn.upper()}): {e}")

        final_payload = {
            "Plant": plant_id,
            "Env": envn,
            "Result": oLPN_detail
            # "Result": all_olpn_results
        }

        return final_payload

    def search_FC_olpn(self):
        olpn_search_payload = self.wave_information.extract_wave_olpn_information_for_FC_packcomplete()

        if not olpn_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        all_olpn_results = []

        for i, payload in enumerate(olpn_search_payload):
            envn = payload['Environment']
            plant_id = str(payload['Plant'])
            olpn_payload = payload['Payload']

            logging.info(f"Processing Task {i + 1}/{len(olpn_search_payload)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_OB_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='oLPNSearch')
                logging.info(f"Sending payload to URL: {api_url}")

                # --- 3. Request Headers ---
                headers = {
                    'Authorization': f'Bearer {bearer_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                }

                # --- 4. Make API Request Call ---
                response = requests.post(api_url, headers=headers, json=olpn_payload, verify=self.ssl_verify)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                logging.info(f"Successfully received response for Plant {plant_id} ({envn.upper()})")
                raw_data = response.json()
                # print(raw_data)
                data = raw_data['data']
                for entry in data:
                    all_olpn_results.append(entry['OlpnId'])

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for Plant {plant_id} ({envn.upper()}): {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for Plant {plant_id} ({envn.upper()}): {e}")

            return all_olpn_results

if __name__ == '__main__':
    search_olpn = Wave_Information_Search()
    lpn_list = search_olpn.search_olpn_payload_for_pack_complete()
    print(lpn_list)

    # search_fc_olpn = Wave_Information_Search()
    # lpn_list = search_fc_olpn.search_FC_olpn_payload()
    # print(lpn_list)