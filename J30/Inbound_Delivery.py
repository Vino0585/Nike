import requests
import logging
import json
from typing import Dict, Any

# Assuming these are the correct import paths
from Payload_generation.Inbound_Delivery_Payload import Inbound_Delivery_Payload
from Environment.WM_Environment import AWM_Env

# Use the logging module for better, more consistent output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def post_asn_to_delivery(payload_info: Dict[str, Any], env_handler: AWM_Env):
    """Sends a single payload to the 'Add ASN to Inbound Delivery' API."""
    environment = payload_info['environment']
    plant_id = payload_info['plant']
    payload_data = payload_info['payload']
    token = payload_info.get('token')

    if not token:
        logging.error(f"No token found for {environment}/{plant_id}. Skipping.")
        return

    try:
        env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = env_handler.get_program_url(program='Add_ASN_To_Inbound_Delivery')
        logging.info(f"Target URL for {plant_id}: {api_url}")

        headers = {
            "Content-Type": "application/json",
            "Organization": str(plant_id),
            "Location": str(plant_id),
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(api_url, json=payload_data, headers=headers, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

        logging.info(f"Successfully added ASN for {plant_id}. Response: {response.json()}")

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred for {plant_id}: {http_err}")
        if http_err.response:
            logging.error(f"Response content: {http_err.response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"A request error occurred for {plant_id}: {req_err}")
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON response from {api_url}")
    except Exception as e:
        logging.error(f"An unexpected error occurred for {plant_id}: {e}")

def pre_allocate_inbound_delivery(payload_info: Dict[str, Any], env_handler: AWM_Env):
    """Sends a trigger to pre-allocate the inbound delivery"""

    environment = payload_info['environment']
    plant_id = payload_info['plant']
    token = payload_info.get('token')
    shipment_id = str(payload_info.get('Shipment_ID'))

    if not token:
        logging.error(f"No token found for {environment}/{plant_id}. Skipping.")
        return

    try:
        env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = env_handler.get_program_url(program='Pre_Allocate_Inbound_Delivery')
        logging.info(f"Target URL for {plant_id}: {api_url}")

        headers = {
                    "Content-Type": "application/json",
                    "selectedOrganization": str(plant_id),
                    "selectedLocation": str(plant_id),
                    "Authorization": f"Bearer {token}"
                 }

        body = {
            "ShipmentId": shipment_id
        }

        response = requests.post(url=api_url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        logging.info(f"Successfully pre-allocated {shipment_id} for {plant_id}. Response: {response_data}")

        messages_obj = response_data.get('messages', {})
        message_list = messages_obj.get('Message', [])
        if message_list:
            first_message = message_list[0]
            if isinstance(first_message, dict):
                description = first_message.get('Description')
                if description:
                    logging.info(f"Server Message for {shipment_id}: {description}")


    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred for {plant_id}: {http_err}")
        if http_err.response:
            logging.error(f"Response content: {http_err.response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"A request error occurred for {plant_id}: {req_err}")
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON response from {api_url}")
    except Exception as e:
        logging.error(f"An unexpected error occurred for {plant_id}: {e}")


def main():
    """
    Generates payloads and sends them to the API.
    """
    payload_generator = Inbound_Delivery_Payload()
    payloads = payload_generator.generate_payloads()

    if not payloads:
        logging.warning("No payloads were generated. Exiting.")
        return

    # Instantiate the environment handler once to be more efficient
    env_handler = AWM_Env()

    for payload_info in payloads:
        post_asn_to_delivery(payload_info, env_handler)
        if payload_info.get('Pre_Allocate') == 'Y':
            pre_allocate_inbound_delivery(payload_info, env_handler)
        else:
            logging.info("No Pre receipt is triggered as its flag is set to N or null")

if __name__ == "__main__":
    main()