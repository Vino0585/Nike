import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests

from Australia_Impact.Inbound.Inbound_payload_generation.Pre_Receipt_Payload import Pre_Reciept_Payload
from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet
from Australia_Impact.Environment.Get_Token import Get_Token
from Australia_Impact.Environment.WM_Environment import AWM_Env
from Australia_Impact.Inbound.Inbound_payload_generation.Execution_Report_Writer import (
    ExecutionReportWriter,
)

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

    @staticmethod
    def _normalize_qty(value) -> int:
        try:
            if value is None or str(value).strip() == "":
                return 0
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return 0

    def _search_inbound_deliveries_for_asns(self, environment: str, plant_id: str, asn_ids: list[str]) -> list[dict]:
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
            shipment_qty_by_id = {}
            for asn_entry in response_data.get("data", []):
                for association in asn_entry.get("ShipmentAsnAssociation") or []:
                    shipment_id = association.get("ShipmentId")
                    if shipment_id:
                        shipment_id = str(shipment_id).strip()
                        qty_value = self._normalize_qty(association.get("ShippedQty"))
                        shipment_qty_by_id[shipment_id] = shipment_qty_by_id.get(shipment_id, 0) + qty_value

            return [
                {"shipment_id": shipment_id, "shipped_qty": qty}
                for shipment_id, qty in shipment_qty_by_id.items()
            ]
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
        if "IB_Delivery_QTY" not in master_df.columns:
            master_df["IB_Delivery_QTY"] = ""

        for idx, row in master_df.iterrows():
            plant_id = str(row.get("Plant", "")).strip()
            environment = str(row.get("Environment", "")).strip()
            asn_id_str = str(row.get("ASNID", "")).strip()

            if not (plant_id and environment and asn_id_str):
                continue

            asn_ids = self._unique_in_order(asn_id_str.split(";"))
            inbound_delivery_details = self._search_inbound_deliveries_for_asns(
                environment=environment,
                plant_id=plant_id,
                asn_ids=asn_ids,
            )
            inbound_deliveries = [entry["shipment_id"] for entry in inbound_delivery_details]
            inbound_delivery_qty = [str(entry["shipped_qty"]) for entry in inbound_delivery_details]
            master_df.at[idx, "InboundDelivery"] = ";".join(inbound_deliveries)
            master_df.at[idx, "IB_Delivery_QTY"] = ";".join(inbound_delivery_qty)

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

    def post_asn_to_delivery(self, payload_info: Dict[str, Any], env_handler: AWM_Env) -> bool:
        """Sends ASN-Shipment associations before pre-allocation."""
        environment = payload_info["environment"]
        plant_id = payload_info["plant"]
        payload_data = payload_info.get("payload")
        token = payload_info.get("token")

        if not token:
            logging.error(f"No token found for {environment}/{plant_id}. Skipping add ASN call.")
            return False
        if not payload_data:
            logging.error(f"No payload data found for {environment}/{plant_id}. Skipping add ASN call.")
            return False

        try:
            env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
            api_url = env_handler.get_program_url(program="Add_ASN_To_Inbound_Delivery")
            logging.info(f"Add ASN target URL for {plant_id}: {api_url}")

            headers = {
                "Content-Type": "application/json",
                "Organization": str(plant_id),
                "Location": str(plant_id),
                "Authorization": f"Bearer {token}",
            }

            response = requests.post(api_url, json=payload_data, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            logging.info(
                f"Successfully added ASN to inbound delivery for {plant_id}. "
                f"Response: {response_data.get('success', 'N/A')}"
            )
            return True

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error during Add ASN for {plant_id}: {http_err}")
            if http_err.response:
                logging.error(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error during Add ASN for {plant_id}: {req_err}")
        except json.JSONDecodeError:
            logging.error(f"Failed to decode Add ASN response from {api_url}")
        except Exception as ex:
            logging.error(f"Unexpected error during Add ASN for {plant_id}: {ex}")

        return False

    def pre_allocate_inbound_delivery(self, payload_info: Dict[str, Any], env_handler: AWM_Env):
        """Sends a trigger to pre-allocate the inbound delivery."""
        environment = payload_info["environment"]
        plant_id = payload_info["plant"]
        token = payload_info.get("token")
        shipment_id = str(payload_info.get("Shipment_ID"))

        if not token:
            logging.error(f"No token found for {environment}/{plant_id}. Skipping.")
            return False

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
            return True

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
        return False

    def send_pre_allocate_inbound_delivery(self):
        run_started_at = datetime.now()
        run_user = ""
        step_records = []
        success_count = 0
        failure_count = 0
        payload_generator = Pre_Reciept_Payload()
        payloads = payload_generator.pre_receipt_generate_payloads()

        if not payloads:
            logging.warning("No payloads were generated. Exiting.")
            return

        run_user = str(payloads[0].get("username", "")).strip()

        env_handler = AWM_Env()
        for payload_info in payloads:
            add_success = self.post_asn_to_delivery(payload_info, env_handler)
            pre_allocate_requested = payload_info.get("Pre_Allocate") == "Y"
            pre_allocate_success = False
            if payload_info.get("Pre_Allocate") == "Y" and add_success:
                pre_allocate_success = self.pre_allocate_inbound_delivery(payload_info, env_handler)
            elif payload_info.get("Pre_Allocate") == "Y" and not add_success:
                logging.error("Skipping Pre-Allocate because Add ASN to Inbound Delivery failed.")
            else:
                logging.info("No Pre receipt is triggered as its flag is set to N or null")

            if add_success and (not pre_allocate_requested or pre_allocate_success):
                success_count += 1
            else:
                failure_count += 1

            asn_ids = []
            for item in payload_info.get("payload", {}).get("Data", []):
                asn_id = str(item.get("AsnId", "")).strip()
                if asn_id:
                    asn_ids.append(asn_id)
            step_records.append(
                {
                    "Environment": payload_info.get("environment", ""),
                    "Plant": payload_info.get("plant", ""),
                    "ShipmentId": payload_info.get("Shipment_ID", ""),
                    "ASN_IDs": ";".join(asn_ids),
                    "AddASNSuccess": add_success,
                    "PreAllocateRequested": pre_allocate_requested,
                    "PreAllocateSuccess": pre_allocate_success if pre_allocate_requested else "NotRequested",
                }
            )

        self._update_master_input_inbound_deliveries()

        run_ended_at = datetime.now()
        report_path = ExecutionReportWriter().write_step_report(
            step_name="Inbound Delivery and Pre-Allocate",
            run_user=run_user or os.getenv("USER", ""),
            started_at=run_started_at,
            ended_at=run_ended_at,
            status="SUCCESS" if success_count and not failure_count else ("PARTIAL" if success_count else "FAILED"),
            summary={
                "TotalPayloads": len(payloads),
                "SuccessfulPayloads": success_count,
                "FailedPayloads": failure_count,
            },
            records=step_records,
        )
        logging.info(f"Execution document generated: {report_path}")


ib_delivery = Pre_Allocate_Inbound_Delivery()
ib_delivery.send_pre_allocate_inbound_delivery()
