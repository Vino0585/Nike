import logging
from typing import Any
from pathlib import Path
import sys
from datetime import datetime, timedelta

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

        parent_order_data = []
        results = response_data.get("data", {}).get("Results", [])
        for order_data in results:
            row = {
                "OrderId": order_data.get('OrderId'),
                "Plant": order_data.get('OriginFacilityId'),
                "Environment": 'QA'
            }
            parent_order_data.append(row)
        return parent_order_data


    def parse_mhe_parent_order_search(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.mhe_journal_worksheet_extract_parameter()
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
                order_ids = data_row.get("order_ids")

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

    def order_search_custom(self):
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

        original_order_data = []
        for order_data in result:
            order_data_extended = order_data.get('Extended')
            order_data_order_line = order_data.get('OriginalOrderLine')
            for line in order_data_order_line:
                requested_service = line.get('OriginalOrderLineRequestedServices')
                for each_requested_service in requested_service:
                    row = {
                        "Plant": order_data.get('OrgId'),
                        "Environment": 'QA',
                        "OrderId": order_data.get('OriginalOrderId'),
                        "OrderType": order_data.get('OrderType'),
                        "LoadingGroup": order_data_extended.get('LoadingGroup'),
                        "PickupStartDate": self._format_date(order_data.get('PickupStartDateTime')),
                        "PickupEndDate": self._format_date(order_data.get('PickupEndDateTime')),
                        "DeliveryStartDate": self._format_date(order_data.get('DeliveryStartDateTime')),
                        "DeliveryEndDate": self._format_date(order_data.get('DeliveryEndDateTime')),
                        "IDPInstruction": order_data_extended.get('IDPInstruction'),
                        "PrePackGroupCode": line.get('PrePackGroupCode'),
                        "ItemName": line.get("ItemId"),
                        "Qty": line.get("OrderedQuantity"),
                        "Sequence": each_requested_service.get("Sequence"),
                        "ServiceTypeID": each_requested_service.get("ServiceTypeId"),
                        "ProvidedServiceId": each_requested_service.get("ProvidedServiceId"),
                        "ServiceUomId": each_requested_service.get("ServiceUomId")
                    }
                    original_order_data.append(row)
        return original_order_data

if __name__ == '__main__':
    # final_search_order_payload = Search_Order_Payload().parse_parent_order_search()
    # if final_search_order_payload:
    #     import json
    #     for i, payload in enumerate(final_search_order_payload):            num = i + 1
    #         logging.info(f"No {num}: Generated payload")
    #         print(json.dumps(payload, indent=4))

    final_search_order_payload = Search_Order_Payload().order_search_custom()
    if final_search_order_payload:
        import json
        for i, payload in enumerate(final_search_order_payload):
            num = i + 1
            logging.info(f"No {num}: Generated payload")
            print(json.dumps(payload, indent=4))