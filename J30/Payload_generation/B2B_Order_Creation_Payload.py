import logging
from typing import Any

from Payload_generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Payload_generation.Number_Generation import NumberGeneration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Order_Creation_Payload:
    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_order_payloads = []

    @property
    def generate_payloads(self) -> list[Any] | None:
        try:
            list_of_datadict = self.worksheet.create_order_extract_parameters()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation.")
                return []
        except Exception as e:
            logging.error(f"Error: {e}")
            return []

        logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

        self.all_order_payloads = []

        for i, data_row in enumerate(list_of_datadict):
            row_num_in_sheet = i + 1
            logging.info(f"Processing Excel Row {row_num_in_sheet}")

            plant = data_row.get("plant")
            envn = data_row.get("environment")
            user_initial = data_row.get("initial")
            num_of_order = data_row.get("number_of_Orders")
            order_type = data_row.get("order_Type")
            item = data_row.get("item")
            qty = data_row.get("qty")
            d_facility = data_row.get("d_facility")
            pre_pack_code = data_row.get("pre_pack_code")
            vas_code_service_id = data_row.get("vas_code_service_id")
            vas_code_service_uom = data_row.get("vas_code_service_uom")
            service_level = data_row.get("service_level")
            address_1 = data_row.get("address_1")
            city = data_row.get("city")
            state = data_row.get("state")
            postal_code = data_row.get("postal_code")
            country = data_row.get("country")
            first_name = data_row.get("first_name")
            email = data_row.get("email")

            order_ids = self.number_gen.order_number_generation(num_of_order, envn, user_initial)
            if not order_ids:
                logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Number of Orders' is 0 or invalid entry is given")
                continue

            for order_index, current_order_id in enumerate(order_ids):
                logging.info(f"Order {current_order_id}:")
                order_line_list = self.build_order_line_list_for_order(

            order_payload = {
                "OrderType": order_type,
                "OriginFacilityId": plant,
                "OriginalOrderId": "CFVAS3386734",
                "IncotermId": "DDP",
                "ResidentialDestination": true,
                "MaximumStatus": "0500",
                "MinimumStatus": "0500",
                "PickupEndDateTime": "2025-04-07T13:28:11",
                "PickupStartDateTime": "2025-04-04T13:28:11",
                "DeliveryEndDateTime": "2025-04-14T13:28:11",
                "DeliveryStartDateTime": "2025-04-05T13:28:11",
                "DestinationFacilityId": "0000314896",
            }

