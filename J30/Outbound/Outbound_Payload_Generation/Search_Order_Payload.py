import logging
from typing import Any
from pathlib import Path
import sys
from datetime import datetime, timedelta

from Outbound.Outbound_Payload_Generation.Search_Order_Payload_Backup import Search_Order_Payload_BackUp

# Ensure the J30 project root is on sys.path so the `Outbound` package can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Search_Order_Payload:

    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.all_search_order_payload = []


    def parse_parent_order_search(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.search_parent_order()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for search order processing.")

            self.all_search_order_payload = []

            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                order_ids = data_row.get("Order_IDs")

                if not plant or not environment or not order_ids:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Plant' or 'Environment', or" 
                                  f"'Order_ID' is missing")
                    return []

                order_id_query_value = "','".join(order_ids)
                payload = {
                              "ViewName": "Order",
                              "Filters": [
                                {
                                  "ViewName": "orders",
                                  "AttributeId": "OrderLine.OriginalOrderId",
                                  "Operator": "=",
                                  "FilterValues": [
                                    order_id_query_value
                                  ]
                                }
                              ],
                              "SortIndicator": None,
                              "TimeZone": "Japan",
                              "MaxCountLimit": 100,
                              "ComponentName": "com-manh-cp-dcorder",
                              "Size": 10,
                              "Sort": "CreatedTimestamp"
                            }

                final_payload = {
                    'Plant': plant,
                    'Environment': environment,
                    'Payload': payload
                }
                self.all_search_order_payload.append(final_payload)
            return self.all_search_order_payload

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")


    def parse_major_order_response(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error(f"INFO: No data returned from search order payload generation.")
            return []

        results = response_data.get("data")
        plant = None
        environment = None
        order_id = []
        for order_data in results:
            plant = order_data.get('OriginFacilityId')
            environment = 'QA'
            order_id.append(order_data.get('OrderId'))

        row = {
            "Plant": plant,
            "Environment": environment,
            "OrderId": order_id
        }
        return row


    def parse_mhe_parent_order_search(self, environemnt, plant_id, order_ids) -> list[Any]:
        self.all_search_order_payload = []

        plant = plant_id
        environment = environemnt
        order_ids = order_ids

        if not plant or not environment or not order_ids:
            logging.error(f"INFO: Skipping as 'Plant' or 'Environment', or" 
                          f"'Order_ID' is missing")
            return []

        order_id_query_value = ','.join(order_ids.split(';'))
        payload = {
            "Query": f"OriginalOrderId in ('{order_id_query_value}')"""
        }
        final_payload = {
            'Plant': plant,
            'Environment': environment,
            'Payload': payload
        }
        self.all_search_order_payload.append(final_payload)
        return self.all_search_order_payload

    def order_search(self):
        try:
            list_of_datadict = self.worksheet.search_parent_order()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for search order processing.")

            self.all_search_order_payload = []

            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                raw_order_ids = data_row.get("Order_IDs")
                order_ids = [str(oid).zfill(10) for oid in raw_order_ids] if isinstance(raw_order_ids, list) else []

                if not plant or not environment or not order_ids:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Plant' or 'Environment', or"
                                  f"'Order_ID' is missing")
                    return []
                order_id_split = order_ids[0].split(';')
                order_id_query_value = "','".join(order_id_split)
                payload = {
                    "Query": f"OriginalOrderId in ('{order_id_query_value}')"""
                }
                final_payload = {
                    'Plant': plant,
                    'Environment': environment,
                    'Payload': payload
                }
                self.all_search_order_payload.append(final_payload)
            return self.all_search_order_payload

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")


    def parent_order_search(self):
        try:
            list_of_datadict = self.worksheet.search_parent_order()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for search order processing.")

            self.all_search_order_payload = []

            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                raw_order_ids = data_row.get("Order_IDs")
                order_ids = [str(oid).zfill(10) for oid in raw_order_ids] if isinstance(raw_order_ids, list) else []

                if not plant or not environment or not order_ids:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Plant' or 'Environment', or"
                                  f"'Order_ID' is missing")
                    return []
                order_id_split = order_ids[0].split(';')
                order_id_query_value = "','".join(order_id_split)
                payload = {
                    "Query": f"OrderLine.OriginalOrderId in ('{order_id_query_value}')"""
                }
                final_payload = {
                    'Plant': plant,
                    'Environment': environment,
                    'Payload': payload
                }
                self.all_search_order_payload.append(final_payload)
            return self.all_search_order_payload

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

    def _format_date(self, date_str: str) -> str:
        if not date_str:
            return None
        try:
            # Parse ISO format (e.g., 2026-02-12T09:00:00)
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Add 9 hours to convert UTC to JST
            dt_jst = dt + timedelta(hours=9)
            
            # Format to: February 12, 2026 9:00:00 PM GMT+9
            formatted = dt_jst.strftime("%B %d, %Y %I:%M:%S %p")
            return f"{formatted} GMT+9"
        except ValueError:
            return date_str

    def parse_original_order_response(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error(f"INFO: No data returned from search order payload generation.")
            return []

        result = response_data.get("data")

        status_code= {
            "0500": "Draft",
            "1000": "Released",
            "2090": "Allocated",
            "7200": "Packed",
            "7800": "Loaded",
            "8000": "Shipped",
            "9000": "Cancelled"
        }

        original_order_data = []
        for order_data in result:
            order_status = status_code.get(order_data.get('MaximumStatus'))
            order_data_extended = order_data.get('Extended')
            order_data_order_line = order_data.get('OriginalOrderLine')
            order_delivery_address = order_data.get('DestinationAddress')
            order_line_extended = order_data_order_line[0]['Extended']
            for line in order_data_order_line:
                requested_service = line.get('OriginalOrderLineRequestedServices')
                # for each_requested_service in requested_service:
                row = {
                    # "Plant": order_data.get('OrgId'),
                    # "Environment": 'QA',
                    "OrderId": order_data.get('OriginalOrderId'),
                    # "OrderType": order_data.get('OrderType'),
                    # "ApptIndic": order_data_extended.get("AppointmentSchedulingIndicator"),
                    # "Load/Fill-in": order_data_extended.get("LoadInFillInIndicator"),
                    "Status": order_status,
                    "LoadingGroup": order_data_extended.get('LoadingGroup'),
                    # "ShipTo": order_data.get('DestinationFacilityId'),
                    # "Shipment": order_data.get("DesignatedShipmentId"),
                    # "Stop": order_data.get("DesignatedStopId"),
                    # "Carrier": order_data_extended.get("CarrierCode"),
                    "ServiceLvl": order_data_extended.get("ServiceLevelCode"),
                    # "HUB": order_data_extended.get("CarrierHubCode"),
                    # "SUB_HUB": order_data_extended.get("CarrierSubHubCode"),
                    "AssignedHub": order_data_extended.get('AssignedCarrierHubId'),
                    # "SO_NBR": order_data_extended.get("SalesOrderNumber"),
                    # "PickupStartDate": self._format_date(order_data.get('PickupStartDateTime')),
                    # "PickupEndDate": self._format_date(order_data.get('PickupEndDateTime')),
                    # "DeliveryStartDate": self._format_date(order_data.get('DeliveryStartDateTime')),
                    # "DeliveryEndDate": self._format_date(order_data.get('DeliveryEndDateTime')),
                    # "PostalCode": order_delivery_address['PostalCode'],
                    # "ExtDeliverySDTM": self._format_date(order_data_extended.get("DeliveryStartDateTime")),
                    # "ExtDeliveryEDTM": self._format_date(order_data_extended.get("DeliveryEndDateTime")),
                    "CRD": order_data_extended.get('CustomerRequestedTimestamp'),
                    # "IDPInstruction": order_data_extended.get('IDPInstruction'),
                    # "Cancel_Date": self._format_date(order_data_extended.get("LastShipmentTimestamp")),
                    # "TransitTime": order_data_extended.get("TransitTime"),
                    # "LastShipmentTime": self._format_date(order_data_extended.get("LastShipmentTimestamp")),
                    # "PrePackCode": line.get('PrePackGroupCode'),
                    "ItemName": line.get("ItemId"),
                    "Qty": line.get("OrderedQuantity"),
                    "FullPrice": order_line_extended.get("FullPrice"),
                    "DiscountPrice": order_line_extended.get("DiscountPrice"),
                    "GiftBag": order_data_extended.get("NikeGiftBagPrice"),
                    "ExternalGiftBagPrice": order_data_extended.get("ExternalGiftBagPrice"),
                    "ShippingCharge": order_data_extended.get("ShippingCharge")
                    # "Sequence": each_requested_service.get("Sequence"),
                    # "ServiceTypeID": each_requested_service.get("ServiceTypeId"),
                    # "ProvidedServiceId": each_requested_service.get("ProvidedServiceId"),
                    # "ServiceUomId": each_requested_service.get("ServiceUomId")
                }
                original_order_data.append(row)
        return original_order_data

    def parse_parent_order_line_response(self, parent_order_line_response_data: dict) -> list:
        if not parent_order_line_response_data.get("data"):
            logging.error(f"INFO: No parent order data returned from search order payload generation, "
                          f"check if your order is shipment planned!")
            return []
        result = parent_order_line_response_data.get("data")

        status_code= {
            "0500": "Draft",
            "1000": "Released",
            "2090": "Allocated",
            "7200": "Packed",
            "7800": "Loaded",
            "8000": "Shipped"
        }


        parent_order_line_data = []
        for order_data in result:
            order_data_order_line = order_data.get('OrderLine')
            order_data_extended = order_data.get('Extended')
            for line in order_data_order_line:
                row = {
                    "OrderId": order_data.get("OrderId", "NA as order is in draft status"),
                    "Status": line.get("Status", "NA"),
                    "Original_Order_id": line.get("OriginalOrderId", '0'),
                    "WaveID": line.get("OriginalOrderPlanningRunId", 'NA as order is not waved yet'),
                    "SpurID": order_data_extended.get('SpurId')
                }
                parent_order_line_data.append(row)
        return parent_order_line_data

    def parent_order_search_for_tran_log(self):
        try:
            list_of_datadict = self.worksheet.wave_information_extract()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for search order processing.")

            self.all_search_order_payload = []

            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                wave_id = data_row.get("Wave_number")
                if not plant or not environment or not wave_id:
                    logging.error(
                        f"INFO: Skipping row {row_num_in_sheet} due to missing Plant, Environment, or Wave_number.")
                    return []

                wave_id_split = wave_id.split(';')
                wave_id_query_value = "','".join(wave_id_split)

                payload = {
                    "Query": f"OrderLine.OrderPlanningRunId in ('{wave_id_query_value}')"
                }
                final_payload = {
                    'Plant': plant,
                    'Environment': environment,
                    'Payload': payload
                }
                self.all_search_order_payload.append(final_payload)
            return self.all_search_order_payload

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

    def parse_parent_order_line_response_for_tran_log_wave(self, parent_order_line_response_data: dict) -> list:
        if not parent_order_line_response_data.get("data"):
            logging.error(f"INFO: No parent order data returned from search order payload generation, "
                          f"check if your order is shipment planned!")
            return []
        result = parent_order_line_response_data.get("data")

        parent_order_line_data = []
        for order_data in result:
            order_data_order_line = order_data.get('OrderLine')
            for line in order_data_order_line:
                row = {
                    "OrderId": order_data.get("OrderId", "NA as order is in draft status"),
                    "Original_Order_id": line.get("OriginalOrderId", '0'),
                }
                parent_order_line_data.append(row)
        return parent_order_line_data

if __name__ == '__main__':
    # final_search_order_payload = Search_Order_Payload().parse_parent_order_search()
    # if final_search_order_payload:
    #     import json
    #     for i, payload in enumerate(final_search_order_payload):            num = i + 1
    #         logging.info(f"No {num}: Generated payload")
    #         print(json.dumps(payload, indent=4))

    # final_search_order_payload = Search_Order_Payload().parse_parent_order_line_response()
    # if final_search_order_payload:
    #     import json
    #     for i, payload in enumerate(final_search_order_payload):
    #         num = i + 1
    #         logging.info(f"No {num}: Generated payload")
    #         print(json.dumps(payload, indent=4))

    final_search_order_payload = Search_Order_Payload().order_search()
    print(final_search_order_payload)