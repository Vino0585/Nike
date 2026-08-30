import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests

from Australia_Impact.Inbound.Inbound_payload_generation.Pre_Receipt_Payload import Pre_Reciept_Payload
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet
from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Pre_Allocate_Inbound_Delivery:
    @staticmethod
    def _unique_in_order(values):
        seen = set()
        unique_values = []
        for value in values:
            normalized = str(value).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_values.append(normalized)
        return unique_values

    def _search_inbound_deliveries_for_asns(self, environment: str, plant_id: str, asn_ids: list[str]) -> list[str]:
        if not asn_ids:
            return []

        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()
        if not bearer_token:
            logging.error(f"Failed to get bearer token for {environment}/{plant_id}.")
            return []

        env_handler = AWM_Env()
        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
        api_url = env_handler.get_program_url(program="ASN_Search")

        headers = {
            "Content-Type": "application/json",
            "organization": str(plant_id),
            "location": str(plant_id),
            "Authorization": f"Bearer {bearer_token}",
        }
        query_values = "','".join(asn_ids)
        payload = {"Query": f"AsnId in ('{query_values}')"}

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            shipment_ids = []
            for asn_entry in response_data.get("data", []):
                for association in asn_entry.get("ShipmentAsnAssociation") or []:
                    shipment_id = association.get("ShipmentId")
                    if shipment_id:
                        shipment_ids.append(str(shipment_id))
            return self._unique_in_order(shipment_ids)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error while searching ASN for {plant_id}: {http_err}")
            if http_err.response:
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error while searching ASN for {plant_id}: {req_err}")
        except json.JSONDecodeError:
            logging.error(f"Failed to decode ASN search response from {api_url}")
        except Exception as ex:
            logging.error(f"Unexpected error during ASN search for {plant_id}: {ex}")

        return []

    def _update_master_input_inbound_deliveries(self):
        worksheet = Worksheet()
        workbook_path = Path(worksheet.master_file_path)
        if not workbook_path.exists():
            logging.error(f"Worksheet not found: {workbook_path}")
            return

        try:
            master_df = pd.read_excel(workbook_path, sheet_name="MasterInput", dtype=str).fillna("")
        except Exception as ex:
            logging.error(f"Failed to read MasterInput from {workbook_path}: {ex}")
            return

        if master_df.empty:
            logging.info("MasterInput is empty. No InboundDelivery update needed.")
            return

        if "InboundDelivery" not in master_df.columns:
            master_df["InboundDelivery"] = ""

        for idx, row in master_df.iterrows():
            plant_id = str(row.get("Plant", "")).strip()
            environment = str(row.get("Environment", "")).strip()
            asn_id_str = str(row.get("ASNID", "")).strip()

            if not (plant_id and environment and asn_id_str):
                continue

            asn_ids = self._unique_in_order(asn_id_str.split(";"))
            inbound_deliveries = self._search_inbound_deliveries_for_asns(
                environment=environment,
                plant_id=plant_id,
                asn_ids=asn_ids,
            )
            master_df.at[idx, "InboundDelivery"] = ";".join(inbound_deliveries)

        try:
            with pd.ExcelWriter(
                workbook_path,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                master_df.to_excel(writer, sheet_name="MasterInput", index=False)
            logging.info(f"Updated MasterInput InboundDelivery values in {workbook_path}")
        except Exception as ex:
            logging.error(f"Failed to write MasterInput updates to {workbook_path}: {ex}")

    def pre_allocate_inbound_delivery(self, payload_info: Dict[str, Any], env_handler: AWM_Env):
        """Sends a trigger to pre-allocate the inbound delivery."""
        environment = payload_info["environment"]
        plant_id = payload_info["plant"]
        token = payload_info.get("token")
        shipment_id = str(payload_info.get("Shipment_ID"))

        if not token:
            logging.error(f"No token found for {environment}/{plant_id}. Skipping.")
            return

        try:
            env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
            api_url = env_handler.get_program_url(program="Pre_Allocate_Inbound_Delivery")
            logging.info(f"Target URL for {plant_id}: {api_url}")

            headers = {
                "Content-Type": "application/json",
                "selectedOrganization": str(plant_id),
                "selectedLocation": str(plant_id),
                "Authorization": f"Bearer {token}",
            }
            body = {"ShipmentId": shipment_id}

            response = requests.post(url=api_url, headers=headers, json=body, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            logging.info(
                f"Successfully pre-allocated {shipment_id} for {plant_id}. "
                f"Response: {response_data.get('success', 'N/A')}"
            )

            messages_obj = response_data.get("messages", {})
            message_list = messages_obj.get("Message", [])
            if message_list:
                first_message = message_list[0]
                if isinstance(first_message, dict):
                    description = first_message.get("Description")
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
        except Exception as ex:
            logging.error(f"An unexpected error occurred for {plant_id}: {ex}")

    def send_pre_allocate_inbound_delivery(self):
        payload_generator = Pre_Reciept_Payload()
        payloads = payload_generator.pre_receipt_generate_payloads()

        if not payloads:
            logging.warning("No payloads were generated. Exiting.")
            return

        env_handler = AWM_Env()
        for payload_info in payloads:
            if payload_info.get("Pre_Allocate") == "Y":
                self.pre_allocate_inbound_delivery(payload_info, env_handler)
            else:
                logging.info("No Pre receipt is triggered as its flag is set to N or null")

        self._update_master_input_inbound_deliveries()


ib_delivery = Pre_Allocate_Inbound_Delivery()
ib_delivery.send_pre_allocate_inbound_delivery()
