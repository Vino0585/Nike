import logging
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from collections import defaultdict
import pandas as pd
from pathlib import Path


import json
from Inventory.Inventory_Payload_Generation.Tran_Log_Detail_Payload import Tran_Log_Detail_Payload
import requests

class Tran_Log_Detail:
    # Initialize Tran Log payload generator and prebuilt payload list.
    def __init__(self):
        self.tran_log_detail_payload = Tran_Log_Detail_Payload()
        self.all_tran_log_detail_payload = self.tran_log_detail_payload.create_tran_log_detail_payload()

    # Send Tran Log detail requests, parse payload content, and export results.
    def send_tran_log_detail(self):
        if not self.all_tran_log_detail_payload:
            logging.error("No payload was received from Tran_log_detail_payload. Please check that file.")
            return None

        payloads_by_group = defaultdict(list)
        for package in self.all_tran_log_detail_payload:
            if not isinstance(package, dict):
                logging.error("WARNING: Skipping package as it's not a valid dictionary")
                continue

            env = package.get('Environment')
            plant_id = package.get('Plant')
            payloads = package.get('msg_id')

            if env and plant_id and payloads:
                payloads_by_group[(env, plant_id)].append(payloads)
            else:
                logging.error(f"WARNING: Skipping malformed package: {package}")

        env_handler = AWM_Env()

        response_result = []
        all_result_data = []
        for (environment, plant_id), payloads in payloads_by_group.items():
            logging.info(f"Processing {len(payloads)} Payloads for Env: {environment.upper()} / Plant: {plant_id}")
            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info(f"Successfully retrieved token for {environment.upper()} env, Plant {plant_id}.")

                env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
                api_url = env_handler.get_program_url(program="Tran_log_detail")
                logging.info(f"Sending payloads to URL: {api_url}")

                header = {
                    "content-type": "application/json",
                    "selectedorganization": str(plant_id),
                    "selectedlocation": str(plant_id),
                    "authorization": f'Bearer {bearer_token}'
                }

                for i, payload_to_send in enumerate(payloads):
                    try:
                        logging.info(f"[{environment.upper()}] Processing Payload {i + 1}/{len(payloads)}")
                        full_url = f"{api_url}/{payload_to_send}"
                        logging.info(f"Sending GET request to: {full_url}")

                        response = requests.get(url=full_url, headers=header)
                        response.raise_for_status()
                        response_data = response.json()

                        # The 'payload' is a string that contains another JSON object. We need to parse it twice.
                        payload_string = response_data.get('data', [{}])[0].get('payload')
                        
                        logging.info(f"Successfully received response for message ID {payload_to_send}.")

                        if not payload_string:
                            logging.warning("Payload content was empty or not found in the response.")
                            continue

                        # Step 1: Parse the outer string to get to 'OriginalPayload'
                        outer_payload_dict = json.loads(payload_string)
                        
                        # Step 2: Get the inner JSON string and parse it into a dictionary
                        original_payload_str = outer_payload_dict.get('OriginalPayload')
                        if not original_payload_str:
                            logging.warning("'OriginalPayload' key not found in the payload content.")
                            continue
                            
                        inner_payload_dict = json.loads(original_payload_str)

                        # Step 3: Now you can safely extract the information you need
                        pix_fields = inner_payload_dict.get('ExportDocuments', [{}])[0].get('PIXFields', {})
                        item_defn = inner_payload_dict.get('ExportDocuments', [{}])[0].get('ItemDefinition', {})

                        po_id = pix_fields.get('PurchaseOrderId')
                        asn_id = pix_fields.get('AsnId')
                        created_by = pix_fields.get('CreatedBy')
                        Tran_nbr = inner_payload_dict.get('ExportDocuments', [{}])[0].get('TransactionNumber')
                        item_id = item_defn.get('ItemId')
                        from_bucket = pix_fields.get('FromInventoryBucket')
                        to_bucket = pix_fields.get('ToInventoryBucket')
                        ilpn_id = pix_fields.get('IlpnId')
                        qty = pix_fields.get('Quantity')
                        try:
                            from_condition_code = pix_fields.get('ConditionCodes')[1]['FromConditionCodes'][0]['ConditionCodeId']
                        except:
                            from_condition_code = 'NA'
                        try:
                            to_condition_code = pix_fields.get('ConditionCodes')[0]['ToConditionCodes'][0]['ConditionCodeId']
                        except:
                            to_condition_code = 'NA'

                        export_info = {
                            'Transaction_nbr': Tran_nbr,
                            'ASN': asn_id,
                            'PO_NBR': po_id,
                            'Item_id': item_id,
                            'LPN_ID': ilpn_id,
                            'Qty': qty,
                            'From_CC': from_condition_code,
                            'From_Bucket': from_bucket,
                            'To_CC': to_condition_code,
                            'To_Bucket': to_bucket,
                            'UserID': created_by
                        }

                        all_result_data.append(export_info)

                        logging.info(f"Extracted Data -> iLPN: {ilpn_id}, PO: {po_id}, User: {created_by}")
                        
                    except requests.exceptions.RequestException as e:
                        logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            logging.error(f"API Response Body: {e.response.text}")
                    except Exception as e:
                        logging.error(f"ERROR: An unexpected error occurred for payload {i + 1}: {e}")
            except Exception as e:
                logging.error(f"FATAL ERROR: Could not process batch for env {environment.upper()}/plant {plant_id}. Error: {e}")

        logging.info(f"Tran log Detail Processing Finished")
        logging.info(f"Total of {len(response_result)} payloads were sent successfully.")

        # Exporting to table.

        if not all_result_data:
            logging.error("Script finished, but no results were collected from any API calls")
            return

        logging.info(f"Consolidated Search Results")
        try:
            results_df = pd.DataFrame(all_result_data)
            results_df = results_df.sort_values(by=['Transaction_nbr', 'Item_id'])
            print(results_df.to_string(index=False))

            # 2. Export the DataFrame to an Excel file (Improved Path Handling)
            # Create a Path object for the output directory.
            output_dir = Path("../Output_files")
            # Check if directory exist.
            output_dir.mkdir(parents=True, exist_ok=True)
            # Define the full path to the output file.
            output_filepath = output_dir / "Tran_log_Detail_Results.xlsx"
            results_df.to_excel(output_filepath, sheet_name='TranLogDetail', index=False)

            logging.info(f"Successfully exported {len(results_df)} results to '{output_filepath}'")
            # --- End of suggested change ---

        except Exception as e:
            logging.info(f"ERROR: Failed to generate or export the final report: {e}")

        logging.info(f"Tran Log Detail Processing Finished")
        logging.info(f"Total of {len(response_result)} payloads were sent successfully.")


if __name__ == "__main__":
    Tran_Log_Detail_Info = Tran_Log_Detail()
    Tran_Log_Detail_Info.send_tran_log_detail()
