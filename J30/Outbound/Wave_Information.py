import requests
import logging
import sys
import os
import urllib3
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning

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

    # Initialize wave payload helper and SSL verification behavior.
    def __init__(self):
        self.wave_information = Wave_Information_Payload()
        self.ssl_verify = self._get_ssl_verify_config()

    @staticmethod
    # Resolve SSL verification mode from environment flags/bundle settings.
    def _get_ssl_verify_config():
        disable_ssl_verify = os.getenv("NIKE_DISABLE_SSL_VERIFY", "").strip().lower() in {"1", "true", "yes", "y"}
        ca_bundle = os.getenv("NIKE_CA_BUNDLE", "").strip() or os.getenv("REQUESTS_CA_BUNDLE", "").strip()
        if disable_ssl_verify:
            urllib3.disable_warnings(InsecureRequestWarning)
        return False if disable_ssl_verify else (ca_bundle if ca_bundle else True)

    # Search oLPN data by wave and export flattened results to Excel.
    def search_olpn_payload(self):
        olpn_search_payload = self.wave_information.extract_wave_olpn_information()

        if not olpn_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        all_olpn_results = []
        seen_olpn_ids = set()

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


    # Search task details by wave and export parsed results to Excel.
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


    # Return oLPN IDs for tran-log flows using wave-based oLPN search.
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

    # Fetch oLPN detail rows for pack-complete message generation.
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
                        if isinstance(olpn_detail_rows, dict):
                            oLPN_detail.append(olpn_detail_rows)
                        elif isinstance(olpn_detail_rows, list):
                            oLPN_detail.extend(
                                detail for detail in olpn_detail_rows if isinstance(detail, dict)
                            )

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

    # Fetch FC-eligible oLPN IDs across all result pages.
    def search_FC_olpn(self):
        olpn_search_payload = self.wave_information.extract_wave_olpn_information_for_FC_packcomplete()

        if not olpn_search_payload:
            logging.error("No payload returned from search order payload file")
            return

        all_olpn_results = []
        seen_olpn_ids = set()

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

                # --- 4. Make API Request Calls (All Pages) ---
                base_payload = dict(olpn_payload)
                page_size = int(base_payload.get("Size", 20) or 20)
                if page_size <= 0:
                    page_size = 20
                starting_page = int(base_payload.get("Page", 0) or 0)

                first_page_payload = dict(base_payload)
                first_page_payload["Size"] = page_size
                first_page_payload["Page"] = starting_page

                response = requests.post(api_url, headers=headers, json=first_page_payload, verify=self.ssl_verify)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                logging.info(f"Successfully received page {starting_page} for Plant {plant_id} ({envn.upper()})")
                raw_data = response.json()

                first_page_data = raw_data.get('data', [])
                for entry in first_page_data:
                    olpn_id = entry.get('OlpnId') if isinstance(entry, dict) else None
                    if olpn_id and olpn_id not in seen_olpn_ids:
                        seen_olpn_ids.add(olpn_id)
                        all_olpn_results.append(olpn_id)

                # Safely convert candidate values to int for page-count math.
                def to_int_or_none(value):
                    try:
                        return int(value)
                    except (TypeError, ValueError):
                        return None

                response_header = raw_data.get("header", {}) if isinstance(raw_data, dict) else {}
                total_count_candidates = [
                    response.headers.get('totalCount'),
                    response.headers.get('TotalCount'),
                    response.headers.get('totalcount'),
                    raw_data.get('totalCount') if isinstance(raw_data, dict) else None,
                    raw_data.get('TotalCount') if isinstance(raw_data, dict) else None,
                    response_header.get('totalCount') if isinstance(response_header, dict) else None,
                    response_header.get('TotalCount') if isinstance(response_header, dict) else None,
                ]
                total_count = None
                for candidate in total_count_candidates:
                    parsed_count = to_int_or_none(candidate)
                    if parsed_count is not None and parsed_count >= 0:
                        total_count = parsed_count
                        break

                total_pages = None
                if total_count is not None:
                    total_pages = max(1, (total_count + page_size - 1) // page_size)
                    logging.info(
                        f"Plant {plant_id} ({envn.upper()}): totalCount={total_count}, "
                        f"pageSize={page_size}, totalPages={total_pages}"
                    )
                else:
                    logging.info(
                        f"Plant {plant_id} ({envn.upper()}): totalCount not found in response; "
                        f"continuing page fetch until last page is reached."
                    )

                page_number = starting_page + 1
                while True:
                    if total_pages is not None and page_number >= total_pages:
                        break

                    paged_payload = dict(base_payload)
                    paged_payload["Size"] = page_size
                    paged_payload["Page"] = page_number
                    page_response = requests.post(
                        api_url,
                        headers=headers,
                        json=paged_payload,
                        verify=self.ssl_verify
                    )
                    page_response.raise_for_status()
                    page_raw_data = page_response.json()
                    page_data = page_raw_data.get('data', [])
                    logging.info(
                        f"Fetched page {page_number} for Plant {plant_id} ({envn.upper()}) "
                        f"with {len(page_data)} row(s)"
                    )
                    for entry in page_data:
                        olpn_id = entry.get('OlpnId') if isinstance(entry, dict) else None
                        if olpn_id and olpn_id not in seen_olpn_ids:
                            seen_olpn_ids.add(olpn_id)
                            all_olpn_results.append(olpn_id)

                    if total_pages is None and len(page_data) < page_size:
                        break

                    page_number += 1

            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for Plant {plant_id} ({envn.upper()}): {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for Plant {plant_id} ({envn.upper()}): {e}")

        return all_olpn_results

if __name__ == '__main__':
    search_olpn = Wave_Information_Search()
    lpn_list = search_olpn.search_FC_olpn()
    print(lpn_list)

    # search_fc_olpn = Wave_Information_Search()
    # lpn_list = search_fc_olpn.search_FC_olpn_payload()
    # print(lpn_list)