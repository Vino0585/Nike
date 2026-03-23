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

class Wave_Information_Payload:
    def __init__(self):
        self.all_wave_information_payload = []
        self.worksheet = Outbound_Worksheet()

    def extract_wave_olpn_information(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.wave_information_extract()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet wave_information_extract method returned None. Halting generation")
                return []
            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for wave information processing.")

            self.all_wave_information_payload = []
            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                wave_id = str(data_row.get("Wave_number"))

                if not plant or not environment or not wave_id:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} due to missing Plant, Environment, or Wave_number.")
                    return []

                wave_id_split = wave_id.split(';')
                wave_id_query_value = "','".join(wave_id_split)

                payload = {
                    "Query": f"OrderPlanningRunId in ('{wave_id_query_value}')"
                }
                final_payload = {
                    'Plant': plant,
                    'Environment': environment,
                    'Payload': payload
                }
                self.all_wave_information_payload.append(final_payload)
            return self.all_wave_information_payload

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return []


    def parse_wave_olpn_information(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error(f"INFO: No data returned from search order payload generation.")
            return []

        result = response_data.get("data")
        lpn_data = []
        for lpn in result:
            lpn_extended = lpn['Extended']
            lpn_detail = lpn['OlpnDetail']
            for detail in lpn_detail:
                row = {
                    "OlpnId": detail['OlpnId'],
                    "Created_by": lpn['CreatedBy'],
                    "Status": lpn["Status"],
                    "Item": detail['ItemId'],
                    "Qty": detail['InitialQuantity'],
                    "Tracking_nbr": lpn['TrackingNumber'],
                    "PickLocn": lpn['PickLocationId'],
                    "PSGroupDest": lpn_extended["PackStationGroupDestination"],
                    "Wave_nbr": lpn['OrderPlanningRunId'],
                    "Carrier": lpn['CarrierId'],
                    "OriginalOrderId": detail['OriginalOrderId'],
                    "AggregatedOrder": detail['OrderId'],
                    "LoadingGroup": lpn_extended['LoadingGroup']
                }
                lpn_data.append(row)
        return lpn_data


    def extract_wave_task_detail_information(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.wave_information_extract()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet wave_information_extract method returned None. Halting generation")
                return []
            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for wave information processing.")

            self.template_structure = {
                "TaskId": None, "ItemId": None, "SourceContainerId": None, "SourceLocationId": None,
               "GenerationCodeId": None, "GenerationNumberId": None, "TypeId": None, "Status": None,
               "TargetLocationId": None, "TargetContainerId": None, "OrderId": None, "CriteriaId": None,
               "OriginalOrderId": None, "Quantity": None, "OrderCriteriaId": None, "OlpnId": None,
               "ShipmentId": None
            }

            self.all_wave_information_payload = []
            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                wave_id = str(data_row.get("Wave_number"))

                if not plant or not environment or not wave_id:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} due to missing Plant, Environment, or Wave_number.")
                    return []

                wave_id_split = wave_id.split(';')
                wave_id_query_value = "','".join(wave_id_split)

                payload = {
                    "Query": f"GenerationNumberId in ('{wave_id_query_value}')"
                             f"AND GenerationCodeId in ('Wave', 'Stream')"
                             f"AND Status in ('1000', '8000')",
                    "Template": self.template_structure
                }

                final_payload = {
                    'Plant': plant,
                    'Environment': environment,
                    'Payload': payload
                }
                self.all_wave_information_payload.append(final_payload)
            return self.all_wave_information_payload

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return []


if __name__ == '__main__':
    final_wave_information_payload = Wave_Information_Payload().extract_wave_olpn_information()
    import json
    print(json.dumps(final_wave_information_payload, indent=2))
