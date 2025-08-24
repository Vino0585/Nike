# This program generates payloads for adding ASNs to Inbound Deliveries.
import requests
import logging
import json
from typing import List, Dict, Any, Optional

# Assuming these are the correct import paths
from Environment.Get_Token import Get_Token
from Inbound.ASN_Search import ASN_Search

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Pre_Reciept_Payload:
    def __init__(self):
        self.get_inbound_delivery = ASN_Search.search_asn_get_ib_delivery()

    def pre_receipt_generate_payloads(self) -> List[Dict[str, Any]]:
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

            # From here get the shipment ID for the ASN.
            shipment_id = self.get_inbound_delivery

            if not shipment_id:
                logging.error(f"Failed to get Shipment ID for {environment}/{plant_id} for ASN {asn_ids_str}. Skipping.")
                continue

            # Use a list comprehension for a cleaner way to create the ASN list
            asn_payload_list = [
                {"AsnId": asn.strip(), "ShipmentId": shipment_id}
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