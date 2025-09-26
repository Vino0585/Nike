import requests
import json
import logging
from pathlib import Path
import pandas as pd

from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Payload_generation.iLPN_Information_Payload import iLPN_Information_Payload

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class iLPN_Information:

    def __init__(self):
        self.output_dir = Path("../Output_files")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_FILENAME = self.output_dir / "iLPN_Information_Results.xlsx"


    def search_lpn_receiving_information(self):
        lpn_search_payload_init = iLPN_Information_Payload()
        search_tasks = lpn_search_payload_init.create_lpn_information_payloads()
        if not search_tasks:
            logging.info("Script finished: No valid search task for LPN Search to process.")
            return

        all_results = []
        exception_input = []
        raw_data = None
        # --- Loop correctly over each task ---
        for i, task in enumerate(search_tasks):
            envn = task['environment']
            plant_id = task['plant']
            lpn_ids = task['LPN_Information']

            logging.info(f"Processing Task {i+1}/{len(search_tasks)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program="iLPN_Information_Receiving")
                logging.info(f"Target URL: {api_url}")

                # --- 3. Request Headers & Payload ---
                headers = {
                    "Content-Type": "application/json",
                    "organization": plant_id,
                    "location": plant_id,
                    "Authorization": f"Bearer {bearer_token}"
                }

                payload = lpn_ids

                # --- 4. API Call ---
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                raw_data = response_data.get("data")

                # --- 5. Process and Collect Response ---
                master_extracted_data = lpn_search_payload_init.parse_master_lpn_response(raw_data)
                if master_extracted_data:
                    logging.info(f"Sucess: Found {len(master_extracted_data)} detail rows for this task")
                    for row in master_extracted_data:
                        output = {
                            "Plant": plant_id,
                            "Environment": envn.upper(),
                            "LPN_ID": row["LPN_ID"],
                            "Diversion_Code": row["Diversion_Code"]
                            }
                        exception_input.append(output)

                report_extracted_data = lpn_search_payload_init.parse_report_lpn_receiving_response(raw_data)
                if report_extracted_data:
                    logging.info(f"Success: Found {len(report_extracted_data)} detail rows for this task")
                    all_results.extend(report_extracted_data)

            except requests.exceptions.HTTPError as http_err:
                logging.error(f"HTTP error occurred: {http_err}")
                if http_err.response:
                    logging.error(f"Response content: {http_err.response.text}")
            except requests.exceptions.RequestException as req_err:
                logging.error(f"A request error occurred: {req_err}")
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")


        # --- 6. Final Export ---
        if not all_results:
            logging.info("Script finished, but no results were collected from any API calls")
            return

        logging.info(f"Consolidating and Exporting Results")
        try:
            # Create the main DataFrame with the parsed results
            df_details = pd.DataFrame(all_results)
            with pd.ExcelWriter(self.OUTPUT_FILENAME, engine='openpyxl') as writer:
                # Write the first sheet
                df_details.to_excel(writer, sheet_name="LPN_Receiving_Details", index=False)

                if raw_data:
                    for each_payload in raw_data:
                        # Convert the entire raw dictionary to a formatted JSON string
                        raw_json_string = json.dumps(each_payload, indent=4)
                        # Create a simple DataFrame to hold this string
                        df_raw = pd.DataFrame({'Raw_Payload': [raw_json_string]})

                        # Write the second sheet
                        df_raw.to_excel(writer, sheet_name="Raw_LPN_Receiving_Payload", index=False)
                        logging.info("Raw Payload updated in Excel Sheet: Raw_LPN_Payload")

            logging.info(f"Successfully exported {len(df_details)} total rows to '{self.OUTPUT_FILENAME}'")

        except Exception as e:
            logging.error(f" Error exporting final report to Excel: {e}")

        if exception_input:
            logging.info(f"Consolidating and Exporting Exception Input")

            try:
                report_df = pd.DataFrame(exception_input)
                output_dir = Path("../Input_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "WorkSheet.xlsx"

                with pd.ExcelWriter(output_filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    lpn_df = report_df.rename(columns={"LPN_ID": "LPNID", "Diversion_Code": "DiversionCodeId"})
                    lpn_df.to_excel(writer, sheet_name='Exception_Input', index=False)

                logging.info(f"Successfully created multi-sheet report: {output_filepath}")

            except Exception as e:
                logging.error(f"ERROR: Failed to create multi-sheet Excel report. Error: {e}")
        else:
            logging.info("No data was successfully processed to generate an input sheet.")

    # def search_lpn_inventory_information(self):
    #     lpn_search_payload_init = iLPN_Information_Payload()
    #     search_tasks = lpn_search_payload_init.create_lpn_information_payloads()
    #     if not search_tasks:
    #         logging.info("Script finished: No valid search task for LPN Search to process.")
    #         return
    #
    #     all_results = []
    #     exception_input = []
    #     raw_data = None
    #     # --- Loop correctly over each task ---
    #     for i, task in enumerate(search_tasks):
    #         envn = task['environment']
    #         plant_id = task['plant']
    #         lpn_ids = task['LPN_Information']
    #
    #         logging.info(f"Processing Task {i + 1}/{len(search_tasks)}: Plant {plant_id} ({envn.upper()})")
    #
    #         try:
    #             # --- 1. Authentication ---
    #             token_handler = Get_Token(env=envn.lower(), plant=plant_id)
    #             bearer_token = token_handler.get_bearer()
    #             logging.info("Successfully retrieved token.")
    #
    #             # --- 2. URL Setup ---
    #             awm_env = AWM_Env()
    #             awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
    #             api_url = awm_env.get_program_url(program="iLPN_Information_Inventory")
    #             logging.info(f"Target URL: {api_url}")
    #
    #             # --- 3. Request Headers & Payload ---
    #             headers = {
    #                 "Content-Type": "application/json",
    #                 "organization": plant_id,
    #                 "location": plant_id,
    #                 "Authorization": f"Bearer {bearer_token}"
    #             }
    #
    #             payload = lpn_ids
    #
    #             # --- 4. API Call ---
    #             response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    #             response.raise_for_status()
    #             response_data = response.json()
    #             raw_data = response_data.get("data")
    #
    #             # --- 5. Process and Collect Response ---
    #             report_extracted_data = lpn_search_payload_init.parse_report_lpn_inventory_response(raw_data)
    #             if report_extracted_data:
    #                 logging.info(f"Success: Found {len(report_extracted_data)} detail rows for this task")
    #                 all_results.extend(report_extracted_data)
    #
    #         except requests.exceptions.HTTPError as http_err:
    #             logging.error(f"HTTP error occurred: {http_err}")
    #             if http_err.response:
    #                 logging.error(f"Response content: {http_err.response.text}")
    #         except requests.exceptions.RequestException as req_err:
    #             logging.error(f"A request error occurred: {req_err}")
    #         except Exception as e:
    #             logging.error(f"An unexpected error occurred: {e}")
    #
    #     # --- 6. Final Export ---
    #     if not all_results:
    #         logging.info("Script finished, but no results were collected from any API calls")
    #         return
    #
    #     logging.info(f"Consolidating and Exporting Results")
    #     try:
    #         # Create the main DataFrame with the parsed results
    #         df_details = pd.DataFrame(all_results)
    #         with pd.ExcelWriter(self.OUTPUT_FILENAME, engine='openpyxl') as writer:
    #             # Write the first sheet
    #             df_details.to_excel(writer, sheet_name="LPN_Receiving_Details", index=False)
    #
    #             if raw_data:
    #                 for each_payload in raw_data:
    #                     # Convert the entire raw dictionary to a formatted JSON string
    #                     raw_json_string = json.dumps(each_payload, indent=4)
    #                     # Create a simple DataFrame to hold this string
    #                     df_raw = pd.DataFrame({'Raw_Payload': [raw_json_string]})
    #
    #                     # Write the second sheet
    #                     df_raw.to_excel(writer, sheet_name="Raw_LPN_Receiving_Payload", index=False)
    #                     logging.info("Raw Payload updated in Excel Sheet: Raw_LPN_Payload")
    #
    #         logging.info(f"Successfully exported {len(df_details)} total rows to '{self.OUTPUT_FILENAME}'")
    #
    #     except Exception as e:
    #         logging.error(f" Error exporting final report to Excel: {e}")
    #
    #     if exception_input:
    #         logging.info(f"Consolidating and Exporting Exception Input")
    #
    #         try:
    #             report_df = pd.DataFrame(exception_input)
    #             output_dir = Path("../Input_files")
    #             output_dir.mkdir(parents=True, exist_ok=True)
    #             output_filepath = output_dir / "WorkSheet.xlsx"
    #
    #             with pd.ExcelWriter(output_filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    #                 lpn_df = report_df.rename(columns={"LPN_ID": "LPNID", "Diversion_Code": "DiversionCodeId"})
    #                 lpn_df.to_excel(writer, sheet_name='Exception_Input', index=False)
    #
    #             logging.info(f"Successfully created multi-sheet report: {output_filepath}")
    #
    #         except Exception as e:
    #             logging.error(f"ERROR: Failed to create multi-sheet Excel report. Error: {e}")
    #     else:
    #         logging.info("No data was successfully processed to generate an input sheet.")
    #

if __name__ == "__main__":
    lpn_search = iLPN_Information()
    response_data = lpn_search.search_lpn_receiving_information()
