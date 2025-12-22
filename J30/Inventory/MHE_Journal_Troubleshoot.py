import requests
import logging
import pandas as pd
from pathlib import Path
import json

from collections import defaultdict
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Inventory.Inventory_Payload_Generation.Troubleshoot_MHE_Journal_Payload import Troubleshoot_MHE_Journal_Payload

# Setup basic logging to provide better feedback than logging.info()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MHE_Journal_Troubleshoot:

    def create_mhe_journal_troubleshoot(self):
        mhe_instance = Troubleshoot_MHE_Journal_Payload()
        raw_payloads = mhe_instance.create_troubleshoot_mhe_journal_payloads()

        if not raw_payloads:
            logging.error("No MHE Journal Payload Found")
            return None

        payloads_by_group = defaultdict(list)
        for package in raw_payloads:
            if not isinstance(package, dict):
                logging.error(f"WARNING: Skipping package as it's not a valid dictionary: {package}")
                continue

            env = package.get('environment')
            plant_id = package.get('plant')
            lpn_list = package.get('lpn_list')
            payload = package.get('MHEJournalPayload')

            if env and plant_id and payload:
                payloads_by_group[(env, plant_id)].append(payload)
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
                api_url = env_handler.get_program_url(program="Message_Journal_Inbound")
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
                        response = requests.post(url=api_url, headers=header, json=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()
                        resp = response_data['data']['Results']
                        response_result.append(response_data.get('success'))
                        logging.info(f"SUCCESS: Payload {i + 1} processed successfully.")

                        # 11. Process and collect the results from the response
                        for entry in resp:
                            header_info = entry.get('headers')
                            # iLPN = entry.get('Stage1.MessagePayload.data.goodsholderId')
                            message_payload_str = entry['Stage1']['MessagePayload']
                            message_payload_dict = json.loads(message_payload_str)

                            goodsholder_id = message_payload_dict["data"]['goodsholderId']
                            RSN_CODE = message_payload_dict["data"]['exceptionReason']

                            if RSN_CODE == 'NO_COMMAND_RECEIVED_TIMEOUT':
                                result_row = {
                                    'Envn': environment.upper(),
                                    'Plant': plant_id,
                                    'MessageID': entry.get('MessageId'),
                                    'LPN_ID': goodsholder_id,
                                    'Message_Type': entry.get('MessageType'),
                                    'Status': entry.get('Status'),
                                    'User': header_info.get('User'),
                                    'Created_on': header_info.get('MessageTimeStamp'),
                                    'RSN_CODE': RSN_CODE
                                }
                                all_result_data.append(result_row)

                    except requests.exceptions.JSONDecodeError:
                        logging.error(f"ERROR: Failed to decode JSON from response for payload {i + 1}.")
                        logging.error(f"Raw Response Text: {response.text}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            logging.error(f"API Response Body: {e.response.text}")
                    except Exception as e:
                        logging.error(f"ERROR: An unexpected error occurred for payload {i + 1}: {e}")
            except Exception as e:
                logging.error(
                    f"FATAL ERROR: Could not process batch for env {environment.upper()}/plant {plant_id}. Error: {e}")

        if not all_result_data:
            logging.error("Script finished, but no results were collected from any API calls")
            return

        logging.info(f"Consolidated Search Results")
        try:
            # Create a pandas DataFrame from the list of result dictionaries
            results_df = pd.DataFrame(all_result_data)

            # Sort the DataFrame by the 'Created_on' column chronologically
            results_df = results_df.sort_values(by=['Created_on'], ascending=False)

            # 1. Print the results to the console in a clean table format
            print(results_df.to_string(index=False))

            # 2. Export the DataFrame to an Excel file (Improved Path Handling)
            # Create a Path object for the output directory.
            output_dir = Path("../Output_files")
            # Check if directory exist.
            output_dir.mkdir(parents=True, exist_ok=True)
            # Define the full path to the output file.
            output_filepath = output_dir / "MHE_Journal_Inbound_results.xlsx"
            results_df.to_excel(output_filepath, sheet_name='MHEJournalResult', index=False)

            logging.info(f"Successfully exported {len(results_df)} results to '{output_filepath}'")
            # --- End of suggested change ---

        except Exception as e:
            logging.info(f"ERROR: Failed to generate or export the final report: {e}")

        logging.info(f"MHE Journal Processing Finished")
        logging.info(f"Total of {len(response_result)} payloads were sent successfully.")

if __name__ == "__main__":
    mhe_journal = MHE_Journal_Troubleshoot()
    mhe_journal.create_mhe_journal_troubleshoot()