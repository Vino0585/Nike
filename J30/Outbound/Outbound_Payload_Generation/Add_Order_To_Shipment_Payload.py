import logging
from typing import Any
from datetime import datetime, timedelta

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Payload_generation.Number_Generation import NumberGeneration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Add_order_to_shipment_payload:
    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_add_order_to_shipment_payloads = []

    def generate_payloads(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.add_order_to_shipment_extract_parameter()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []  # Return empty list on failure

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

            self.all_add_order_to_shipment_payloads = []

            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing Excel Row {row_num_in_sheet}")

                plant = data_row.get("Plant")
                envn = data_row.get("Environment")
                shipment_id = data_row.get("Shipment_ID")
                order_ids = data_row.get("Order_ID")
                carrier_id = data_row.get("Carrier_ID")
                mode = data_row.get("Mode")
                service_level = data_row.get("Service_Level")

                now = datetime.now()
                now_iso = now.isoformat(timespec='seconds')
                future = now + timedelta(days=7)
                future_iso = future.isoformat(timespec='seconds')
                loading_group_id = self.number_gen.loading_group_number()

                if not plant and envn and shipment_id and order_ids:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Plant' or 'Environment', or" 
                                  f"'Shipment_ID' or 'Order_ID' is missing")
                    return []

                all_payloads = []

                for order_id in order_ids:
                    add_order_to_shipment_payload = {
                            "OrderId": order_id,
                            "PickupStartDateTime": now_iso,
                            "PickupEndDateTime": now_iso,
                            "DeliveryStartDateTime": future_iso,
                            "DeliveryEndDateTime": future_iso,
                            "DesignatedCarrierId": carrier_id,
                            "DesignatedModeId": mode,
                            "DesignatedServiceLevelId": service_level,
                            "DesignatedShipmentId": shipment_id,
                            "DesignatedStopId": f"{shipment_id}_1",
                            "Extended": {
                                "AssignedServiceLevelId": service_level,
                                "AssignedCarrierId": carrier_id,
                                "nodeCutOffTimestamp": now_iso,
                                "LoadingGroup": loading_group_id
                            }
                        }
                    all_payloads.append(add_order_to_shipment_payload)

                self.all_add_order_to_shipment_payloads.append({'Plant': plant, 'Environment': envn,
                                                                'Payload': all_payloads})
            return self.all_add_order_to_shipment_payloads

        except Exception as e:
            logging.error(f"Error: {e}")
            return []


# This block is excellent for testing your class in isolation.
if __name__ == "__main__":
    add_order_to_shipment = Add_order_to_shipment_payload()
    final_payloads = add_order_to_shipment.generate_payloads()
    if final_payloads:
        import json
        for i, payloads in enumerate(final_payloads):
            num = i+1
            logging.info(f"No {num} Generated Payload")
            print(json.dumps(payloads, indent=2))