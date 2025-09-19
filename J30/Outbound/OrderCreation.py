import requests
import pandas as pd
import logging

from Payload_generation.Order_Creation_Payload import Order_Creation_Payload
from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env
from collections import defaultdict
from pathlib import Path


# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Order_Creation:

    def __init__(self):
        self.order_generation = Order_Creation_Payload()
        self.final_payloads = self.order_generation.generate_payloads

    def create_orders(self):
        if not self.final_payloads:
            logging.error("No payloads were generated. Please check your Excel input and generator logic.")
            return

        payload_by_env = defaultdict(list)
        plant = None
        for package in self.final_payloads:
            env = package.get('environment')
            payload = package.get('payload')
            if env and payload:
                payload_by_env[env].append(payload)
            else:
                logging.error(f"WARNING: Skipping malformed package: {package}")

        extracted_report_data = []

        for environment, payloads in payload_by_env.items():
            logging.info(f"Processing {len(payloads)} Payloads for Environment: {environment.upper()}")
            if not payloads:
                logging.error(f"WARNING: Skipping empty payload list for environment {environment.upper()}.")
                continue

            try:
                plant_id_for_token = payloads[0].get('OriginFacilityId')
                if not plant_id_for_token:
                    logging.error("FATAL ERROR: Cannot get token. payload for {environment.upper()} "
                                  "is missing 'OrgId'")
                    continue

                token_handler = Get_Token(env=environment.lower(), plant=str(plant_id_for_token))
                bearer_token = token_handler.get_bearer()
                logging.info(f"Successfully retrieved token for {environment.upper()} environment.")

                env_handler = AWM_OB_Env()

                for i, payload_to_send in enumerate(payloads):
                    try:
                        plant_id = payload_to_send['OriginFacilityId']
                        logging.info(
                            f"[{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id}")

                        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
                        url_value = env_handler.get_program_url(program='OrderCreation')
                        logging.info(f"Sending payload to URL: {url_value}")

                        headers = {
                            "content-type": "application/json",
                            "organization": str(plant_id),
                            "location": str(plant_id),
                            "authorization": 'Bearer ' + bearer_token
                        }

                        response = requests.post(url=url_value, headers=headers, json=payload_to_send)
                        response.raise_for_status()

                        response_data = response.json()
                        logging.info(f"Success: {response_data.get('success', 'N/A')}")


                        # -- DATA COLLECTION FOR OUTPUT FILES --
                        order_id = payload_to_send.get('OriginalOrderId')
                        order_type = payload_to_send.get('OrderType')
                        destination_facility = payload_to_send.get('DestinationFacilityId')
                        order_line = payload_to_send.get('OriginalOrderLine', [])
                        if order_line:
                            item_id = order_line[0].get('ItemId')
                            quantity = order_line[0].get('OrderedQuantity')

                            report_entry = {
                                "PLANT": plant_id,
                                "ENVN": environment,
                                "ORDER_ID": order_id,
                                "ORDER_TYPE": order_type,
                                "D_FACILITY": destination_facility,
                                "ITEM_ID": item_id,
                                "QTY": quantity
                            }
                            extracted_report_data.append(report_entry)

                    except KeyError as e:
                        logging.error(f"ERROR: Could not process payload {i + 1}. Data is malformed. Missing key: {e}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
                    except Exception as e:
                        logging.error(f"ERROR: An unexpected error occurred for payload {i + 1}: {e}")

            except Exception as e:
                logging.error(f"FATAL ERROR: Could not process batch for environment {environment.upper()}. Error: {e}")


        if extracted_report_data:
            logging.info("Generating Report")
            try:
                report_df = pd.DataFrame(extracted_report_data)

                # Define the Output path.
                output_dir = Path("../Output_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "Order_Creation_Report.xlsx"

                report_df.to_excel(output_filepath, index=False)
                logging.info(f"Successfully created report: {output_filepath}")
            except Exception as e:
                logging.error(f"Failed to create Excel report. Error: {e}")
        else:
            logging.info("No data was successfully processed to generate a report.")


if __name__ == "__main__":
    order_creation = Order_Creation()
    order_creation.create_orders()