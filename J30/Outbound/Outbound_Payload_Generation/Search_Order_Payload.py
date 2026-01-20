import logging
from typing import Any
from pathlib import Path
import sys

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


if __name__ == '__main__':
    final_search_order_payload = Search_Order_Payload().parse_parent_order_search()
    if final_search_order_payload:
        import json
        for i, payload in enumerate(final_search_order_payload):
            num = i + 1
            logging.info(f"No {num}: Generated payload")
            print(json.dumps(payload, indent=4))