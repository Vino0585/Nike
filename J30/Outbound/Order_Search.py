import requests
import logging
from pathlib import Path
from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env
import pandas as pd
from Outbound.Outbound_Payload_Generation.Search_Order_Payload import Search_Order_Payload

# Setup basic logging to provide better feedback than print()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Outbound_Order_Search:

    def search_parent_order_payload(self):
        order_search_payload = Search_Order_Payload()
        get_payload = order_search_payload.parse_parent_order_search()

        if not get_payload:
            logging.error("No payload returned from search order payload file")
            return None

        all_results = []
        raw_data = None

        for i, payload in enumerate(get_payload):
            envn = payload['Environment']
            plant_id = str(payload['Plant'])
            order_payload = payload['Payload']

            logging.info(f"Processing Task {i+1}/{len(get_payload)}: Plant {plant_id} ({envn.upper()})")

            try:
                # --- 1. Authentication ---
                token_handler = Get_Token(env=envn.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info("Successfully retrieved token.")

                # --- 2. URL Setup ---
                awm_env = AWM_OB_Env()
                awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
                api_url = awm_env.get_program_url(program='ParentOrderSearch')
                logging.info(f"Sending payload to URL: {api_url}")

                # --- 3. Request Headers & Payload ---
                headers = {
                    "Content-Type": "application/json",
                    "organization": plant_id,  # Common practice is to use 'organization' and 'location'
                    "location": plant_id,
                    "Authorization": f"Bearer {bearer_token}"
                }

                # --- 4. API Call ---
                response = requests.post(api_url, json=order_payload, headers=headers, timeout=30)
                response.raise_for_status()
                response_data = response.json()

                # --- 5. Process and Collect Response ---
                extracted_data = order_search_payload.parse_major_order_response(response_data)
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

        # --- 6. Final Export ---
        # This block runs once after all tasks are completed.
        if all_results:
            logging.info("Generating Parent Order Data information in Output_Worksheet excel file")

            try:
                df_order_search = pd.DataFrame(all_results)
                output_dir = Path("../Input_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "Outbound_Worksheet.xlsx"

                with pd.ExcelWriter(output_filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    output_df = df_order_search.rename(columns={"PLANT": '1081', "ENVN": "Environment", "ORDER_ID": "OrderID"})
                    output_df.to_excel(writer, sheet_name='ParentOrder', index=False)
                    logging.info(f"Sucessfully exported parent order to Excel file: {output_filepath}")

            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

        else:
            logging.info("No parent order data available therefore didn't export any data")


if __name__ == '__main__':
    search_order = Outbound_Order_Search()
    search_order.search_order_payload()

