import requests
import logging

from Outbound.Outbound_Payload_Generation.Add_Order_To_Shipment_Payload import Add_order_to_shipment_payload
from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Add_Order_To_Shipment:

    def __init__(self):
        self.add_order_to_shipment_load = Add_order_to_shipment_payload()
        self.final_payloads = self.add_order_to_shipment_load.generate_payloads()

    def add_order_to_shipment(self):
        if not self.final_payloads:
            logging.error("No payloads were generated. Please check your Excel input and generator logic.")
            return

        plant = self.final_payloads[0]["Plant"]
        envn = self.final_payloads[0]['Environment']
        payloads = self.final_payloads[0]['Payload']

        if not plant and envn and payloads:
            logging.error(f"INFO: Skipping row as 'Plant' or 'Environment' or 'Payload' is missing")

        logging.info(f"Processing {len(payloads)} Payloads for Environment: {envn.upper()}")

        try:
            plant_id_for_token = plant
            token_handler = Get_Token(env=envn.lower(), plant=str(plant_id_for_token))
            bearer_token = token_handler.get_bearer()
            logging.info(f"Successfully retrieved token for {envn.upper()} environment.")

            env_handler = AWM_OB_Env()

            for i, payload_to_send in enumerate(payloads):
                try:
                    logging.info(
                        f"[{envn.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id_for_token}")

                    env_handler.get_wm_host(host=envn.lower(), facility=str(plant_id_for_token))
                    url_value = env_handler.get_program_url(program='AddOrderToShipment')
                    logging.info(f"Sending payload to URL: {url_value}")

                    header = {
                        "content-type": "application/json",
                        "organization": str(plant_id_for_token),
                        "location": str(plant_id_for_token),
                        "authorization": 'Bearer ' + bearer_token
                    }

                    response = requests.post(url=url_value, json=payload_to_send, headers=header)
                    response.raise_for_status()

                    response_data = response.json()
                    logging.info(f"Success: {response_data.get('success', 'N/A')}")

                except KeyError as e:
                    logging.error(f"ERROR: Could not process payload {i + 1}. Data is malformed. Missing key: {e}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                    if e.response is not None:
                        logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
                except Exception as e:
                    logging.error(f"ERROR: An unexpected error occurred for payload {i + 1}: {e}")

        except Exception as e:
            logging.error(f"FATAL ERROR: Could not process batch for environment {envn.upper()}. Error: {e}")

if __name__ == '__main__':
    aos = Add_Order_To_Shipment()
    aos.add_order_to_shipment()