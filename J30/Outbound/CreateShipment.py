import requests
import pandas as pd
import logging

from Archive.ImportASNDev import response
from Outbound.Outbound_Payload_Generation.Create_Shipment_Payload import Create_New_Shipment
from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env
from collections import defaultdict
from pathlib import Path

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Create_Shipment:
    def __init__(self):
        self.shipment_generation = Create_New_Shipment()
        self.final_payloads = self.shipment_generation.generate_payloads()

    def create_shipment(self):
        if not self.final_payloads:
            logging.error("No payloads were generated. Please check your Excel input and generator logic.")
            return

        payload_by_env_by_plant = defaultdict(list)
        plant = None
        for package in self.final_payloads:
            env = package.get('environment')
            plant = package.get('plant')
            payload = package.get('payload')
            if env and payload and plant:
                payload_by_env_by_plant[env, plant].append(payload)
            else:
                logging.error(f"WARNING: Skipping malformed package: {package}")

        extracted_report_data = []
        output_data = []  # This will hold one dictionary per successful payload

        for environment, plant, payloads in payload_by_env_by_plant.items():
            logging.info(f"Processing {len(payloads)} Payloads for Environment: {environment.upper()}")
            if not payloads:
                logging.error(f"WARNING: Skipping empty payload list for environment {environment.upper()}.")
                continue

            try:
                plant_id_for_token = plant
                if not plant_id_for_token:
                    logging.info(
                    f"[{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} "
                    f"for Plant {plant_id_for_token}")
                    continue

                token_handler = Get_Token(env=environment.lower(), plant=str(plant_id_for_token))
                bearer_token = token_handler.get_bearer()
                logging.info(f"Successfully retrieved token for {environment.upper()} environment.")

                env_handler = AWM_OB_Env()

                for i, payload_to_send in enumerate(payloads):
                    try:
                        logging.info(
                            f"[{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id_for_token}")

                        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id_for_token))
                        url_value = env_handler.get_program_url(program='CreateShipment')
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

                        # -- DATA COLLECTION FOR OUTPUT FILES --
                        shipment_id = payload_to_send.get('ShipmentId')
                        plant = plant_id_for_token

                        output_row = {
                            "SHIPMENT_ID": shipment_id,
                            "PLANT": plant,
                            "ENVN": environment
                        }
                        output_data.append(output_row)

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


        if output_data:
            logging.info("Generating Master Data information in Output_Worksheet excel file")
            try:
                report_df = pd.DataFrame(output_data)
                output_dir = Path("../Input_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "Outbound_Worksheet.xlsx"

                with pd.ExcelWriter(output_filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    shipment_df = report_df.rename(columns={"SHIPMENT_ID": "ShipmentId", "PLANT": "Plant", "ENVN": "Environment"})
                    shipment_df.to_excel(writer, sheet_name='Shipment_ID',  index=False)
                    logging.info(f"Successfully created multi-sheet report: {output_filepath}")
            except Exception as e:
                logging.error(f"ERROR: Failed to create multi-sheet Excel report. Error: {e}")
        else:
            logging.info("No data was successfully processed to generate an input sheet.")


if __name__ == '__main__':
    create_shipment = Create_Shipment()
    create_shipment.create_shipment()