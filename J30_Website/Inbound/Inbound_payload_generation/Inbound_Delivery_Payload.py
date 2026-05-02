# This program generates payloads for adding ASNs to Inbound Deliveries.
import requests
import logging
import json
from typing import List, Dict, Any, Optional

# Assuming these are the correct import paths
from Environment.Get_Token import Get_Token
from Payload_generation.Worksheet_extract import Worksheet
from Environment.WM_Environment import AWM_Env

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Inbound_Delivery_Payload:

    def __init__(self):
        self.worksheet = Worksheet()
        self.env_handler = AWM_Env()

    def _get_inbound_delivery_id(self, environment: str, plant_id: str, bearer_token: str) -> Optional[str]:
        self.env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = self.env_handler.get_program_url(program="Get_Inbound_Delivery")
        logging.info(f"Requesting Inbound Delivery ID from URL: {api_url}")

        headers = {
            "Content-Type": "application/json",
            "selectedorganization": str(plant_id),
            "selectedlocation": str(plant_id),
            "Authorization": f'Bearer {bearer_token}'
        }

        try:
            response = requests.get(url=api_url, headers=headers, timeout=30)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            response_data = response.json()

            # Safely access nested data to prevent crashes
            shipment_id = response_data.get('data', {}).get('ShipmentId')
            if not shipment_id:
                logging.error(f"Could not find 'ShipmentId' in response for {environment}/{plant_id}.")
                return None

            logging.info(f"Successfully retrieved Inbound Delivery ID: {shipment_id}")
            return str(shipment_id)

        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for {environment}/{plant_id}: {e}")
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON response from {api_url}")

        return None

    def generate_payloads(self) -> List[Dict[str, Any]]:
        worksheet_data = self.worksheet.inbound_delivery_worksheet_extract()
        if not worksheet_data:
            logging.warning("Worksheet extract returned no data.")
            return []

        all_payloads = []
        for entry in worksheet_data:
            plant_id = entry.get("Plant")
            environment = entry.get("Environment")
            asn_ids_str = entry.get("ASN_ID")
            pre_allocate = str(entry.get("Pre_Allocate"))

            if not all([plant_id, environment, asn_ids_str]):
                logging.warning(f"Skipping incomplete worksheet entry: {entry}")
                continue

            token_handler = Get_Token(env=environment.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()
            if not bearer_token:
                logging.error(f"Failed to get bearer token for {environment}/{plant_id}. Skipping.")
                continue

            inbound_delivery_id = self._get_inbound_delivery_id(environment, plant_id, bearer_token)
            if not inbound_delivery_id:
                logging.error(f"Failed to get Inbound Delivery ID for {environment}/{plant_id}. Skipping.")
                continue

            # Use a list comprehension for a cleaner way to create the ASN list
            asn_payload_list = [
                {"AsnId": asn.strip(), "ShipmentId": inbound_delivery_id}
                for asn in asn_ids_str.split(';') if asn.strip()
            ]

            if asn_payload_list:
                full_payload = {
                    'payload': {"Data": asn_payload_list},
                    "environment": environment,
                    "plant": plant_id,
                    "token": bearer_token,
                    "Shipment_ID": inbound_delivery_id,
                    "Pre_Allocate": pre_allocate
                }
                all_payloads.append(full_payload)

        return all_payloads




# if __name__ == "__main__":
#     payload_generator = Inbound_Delivery_Payload()
#
#     # Generate and print the payloads
#     generated_payloads = payload_generator.generate_payloads()
#
#     # Pretty-print the JSON output
#     print(json.dumps(generated_payloads, indent=2))