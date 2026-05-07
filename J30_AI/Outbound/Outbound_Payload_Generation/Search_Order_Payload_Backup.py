import logging
from typing import Any

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Search_Order_Payload_BackUp:

    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.all_search_order_payload = []


    def get_order_info_payload(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.search_parent_order()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for search order processing.")

            self.all_search_order_payload = []

            template_structure = {
                            "OrderId": None, "FacilityId": None,
                            "Extended": {"LoadingGroup": None},
                            "OrderLine": {
                                "ItemId": None, "OriginalOrderedQuantity": None, "DesignatedShipmentId": None,
                                "DesignatedStopId": None, "OriginalOrderId": None
                            }
                            }

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
                          "Query": "OrderLine.OriginalOrderId IN ('" + order_id_query_value + "')",
                          "Template": template_structure
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


    def parse_order_response(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error(f"INFO: No data returned from search order payload generation.")
            return []

        parent_order_data = []
        results = response_data.get("data", [])
        for order_data in results:
            row = {
                "Plant": order_data.get('FacilityId'),
                "Environment": 'QA',
                "OrderId": order_data.get('OrderId'),
                "LoadingGroupID": order_data['Extended']['LoadingGroup'],
                "ShipmentID": order_data['OrderLine']['DesignatedShipmentId'],
                "StopID": order_data['OrderLine']['DesignatedStopId'],
                "OriginalOrderID": order_data['OrderLine']['OriginalOrderId'],
                "ItemID": order_data['OrderLine']['ItemId'],
                "OriginalOrderedQuantity": order_data['OrderLine']['OriginalOrderedQuantity']
            }
            parent_order_data.append(row)
        return parent_order_data


if __name__ == '__main__':
    # final_search_order_payload = Search_Order_Payload().parse_parent_order_search()
    final_search_order_payload = Search_Order_Payload_BackUp().parse_parent_order_search()
    if final_search_order_payload:
        import json
        for i, payload in enumerate(final_search_order_payload):
            num = i + 1
            logging.info(f"No {num}: Generated payload")
            print(json.dumps(payload, indent=4))