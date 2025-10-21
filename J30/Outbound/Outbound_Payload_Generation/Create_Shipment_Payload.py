import logging
from typing import Any
from datetime import datetime, timedelta

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Payload_generation.Number_Generation import NumberGeneration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Create_New_Shipment:
    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_create_shipment_payloads = []


    def generate_payloads(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.create_new_shipment_extract_parameter()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation")
                return []  # Return empty list on failure

            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

            self.all_create_shipment_payloads = []

            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing Excel Row {row_num_in_sheet}")

                plant = data_row.get("plant")
                envn = data_row.get("environment")
                create_shipment = data_row.get("create_shipment")
                carrier = data_row.get("carrier")
                service_level = data_row.get("service_level")
                mode = data_row.get("mode")

                now = datetime.now()
                now_iso = now.isoformat(timespec='seconds')
                future = now + timedelta(days=7)
                future_iso = future.isoformat(timespec='seconds')

                shipment_id = self.number_gen.create_shipment_number()

                if not shipment_id:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Shipment_id' returned null")

                if create_shipment != 'Y':
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Create_Shipment' is not set to 'Y'")

                elif create_shipment == 'Y':
                    shipment_payload = {
                            "ShipmentId": shipment_id, "AssignedCarrierId": carrier,
                            "AssignedServiceLevelId": service_level, "AssignedModeId": mode,
                            "Stop": [
                                {
                                    "StopSequence": 1,
                                    "FacilityId": plant,
                                    "StopActionId": {
                                        "StopActionId": "PU"
                                    },
                                    "PlannedArrivalDateTime": now_iso,
                                    "PlannedDepartureDateTime": future_iso,
                                    "StopId": f"{shipment_id}_1"
                                },
                                {
                                    "StopSequence": 2,
                                    "FacilityId": carrier,
                                    "StopActionId": {
                                        "StopActionId": "DL"
                                    },
                                    "PlannedArrivalDateTime": now_iso,
                                    "PlannedDepartureDateTime": future_iso,
                                    "StopId": f"{shipment_id}_2"
                                }
                            ],
                            "Extended": {
                                "nodeCutOffTimestamp": now_iso
                            },
                            "TotalWeight": 0.218,
                            "WeightUomId": "kg",
                            "TotalVolume": "2100.0000",
                            "VolumeUomId": "cucm"
                        }
                    self.all_create_shipment_payloads.append({'payload': shipment_payload, 'environment': envn, 'plant': plant})
            return self.all_create_shipment_payloads

        except Exception as e:
            logging.error(f"Error: {e}")
            return []




# This block is excellent for testing your class in isolation.
if __name__ == "__main__":
    create_shipment = Create_New_Shipment()
    final_payloads = create_shipment.generate_payloads()
    if final_payloads:
        import json
        for i, payloads in enumerate(final_payloads):
            num = i+1
            logging.info(f"No {num} Generated Payload")
            print(json.dumps(payloads, indent=2))