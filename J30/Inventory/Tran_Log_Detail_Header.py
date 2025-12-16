import requests
import logging
import pandas as pd

from collections import defaultdict
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Inventory.Inventory_Payload_Generation.Tran_Log_Detail_Header_Payload import Tran_log_detail_header

# Setup basic logging to provide better feedback than logging.info()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Tran_Log_Detail_Header_Info:

    def create_tran_log_detail_header_inventory(self):
        tran_log_instance = Tran_log_detail_header()
        raw_payloads = tran_log_instance.construct_tran_log_detail_header_payload()

        if not raw_payloads:
            logging.error("No tran log Payload Found")
            return None

        payloads_by_group = defaultdict(list)
        for package in raw_payloads:
            if not isinstance(package, dict):
                logging.error("WARNING: Skipping package as it's not a valid dictionary")
                continue

            env = package.get('Environment')
            plant_id = package.get('Plant')
            payloads = package.get('Tran_log_detail_payload')

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
                api_url = env_handler.get_program_url(program="Tran_log_detail_header")
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
                        response = requests.post(url=api_url, headers=header, data=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()
                        resp = response_data['data']['Results']
                        response_result.append(response_data.get('success'))
                        logging.info(f"SUCCESS: Payload {i + 1} processed successfully.")

                        for entry in resp:
                            org = entry.get("Organization")
                            msg_type = entry.get("MsgType")
                            msg_id = entry.get("MsgId")
                            trace_id = entry.get("TraceId")

                            payload_to_contruct = {
                                "Plant": org,
                                "Environment": env,
                                "msg_type": msg_type,
                                "msg_id": msg_id,
                                "trace_id": trace_id
                            }
                            all_result_data.append(payload_to_contruct)

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
                logging.error(f"FATAL ERROR: Could not process batch for env {environment.upper()}/plant {plant_id}. Error: {e}")

        if not all_result_data:
            logging.error("Script finished, but no results were collected from any API calls")
            return

        logging.info(f"Consolidated Search Results")
        try:
            results_df = pd.DataFrame(all_result_data)
            results_df = results_df.sort_values(by=['msg_type', 'msg_id'], ascending=False)
            print(results_df.to_string(index=False))

        except Exception as e:
            logging.info(f"ERROR: Failed to generate or export the final report: {e}")

        logging.info(f"Tran log Detail Processing Finished")
        logging.info(f"Total of {len(response_result)} payloads were sent successfully.")

        return all_result_data

if __name__ == "__main__":
    Tran_Log_Detail_Info = Tran_Log_Detail_Header_Info()
    Tran_Log_Detail_Info.create_tran_log_detail_header_inventory()