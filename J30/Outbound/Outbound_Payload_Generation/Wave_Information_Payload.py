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
from Outbound.Outbound_Payload_Generation.Task_Detail_Search import Task_Search_Payload

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Wave_Information_Payload:
    def __init__(self):
        self.all_wave_information_payload = []
        self.worksheet = Outbound_Worksheet()
        self.task_search = Task_Search_Payload()

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

        lpn_status = {
            '1000': 'Created',
            '7000': 'Picked',
            '7200': 'Packed',
            '7800': 'Loaded',
            '7900': 'Pending ShipConfirmation',
            '8000': 'Shipped'
        }

        for lpn in result:
            lpn_extended = lpn['Extended']
            lpn_detail = lpn['OlpnDetail']
            for detail in lpn_detail:
                row = {
                    "OlpnId": detail['OlpnId'],
                    "Created_by": lpn['CreatedBy'],
                    "Status": lpn_status[lpn["Status"]],
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
                             f" AND GenerationCodeId in ('Wave', 'Stream')"
                             f" AND Status in ('1000', '8000')",
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

    def parse_wave_olpn_information_for_tran_log(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error(f"INFO: No data returned from search order payload generation.")
            return []

        result = response_data.get("data")
        lpn_data = []

        for lpn in result:
            lpn_detail = lpn['OlpnDetail']
            for detail in lpn_detail:
                lpn_data.append(detail['OlpnId'])
        return lpn_data

    def extract_wave_olpn_information_for_pack_message(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.wave_information_extract()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet wave_information_extract method returned None. Halting generation")
                return []
            logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for wave information processing.")

            template_structure = {
                "OlpnDetail": [
                    {
                        "OlpnId": None,
                        "ItemId": None,
                        "InitialQuantity": None,
                        "OrderId": None,
                    }
                ]
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

                get_fc_eligible_olpn = self.task_search.search_task_detail_by_wave_nbr_FC_packcomplete(
                    # search_by_wave_nbr=wave_id,
                    environment=str(environment),
                    plant_id=str(plant)
                )
                fc_eligible_olpn_values = []
                if isinstance(get_fc_eligible_olpn, list):
                    fc_eligible_olpn_values = [str(olpn).strip() for olpn in get_fc_eligible_olpn if str(olpn).strip()]
                elif get_fc_eligible_olpn is not None and str(get_fc_eligible_olpn).strip():
                    fc_eligible_olpn_values = [str(get_fc_eligible_olpn).strip()]

                wave_id_split = wave_id.split(';')
                wave_id_query_value = "','".join(wave_id_split)

                query_list = [f"OrderPlanningRunId in ('{wave_id_query_value}') AND Status in ('7000')"]
                if fc_eligible_olpn_values:
                    fc_eligible_olpn_query_value = "','".join(fc_eligible_olpn_values)
                    query_list.append(f"OlpnId in ('{fc_eligible_olpn_query_value}')")
                for query in query_list:
                    payload = {
                        "Query": query,
                        "Template": template_structure
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

    def extract_wave_olpn_information_for_FC_packcomplete(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.wave_information_extract()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet wave_information_extract method returned None. Halting generation")
                return []
            logging.debug(f"Successfully extracted {len(list_of_datadict)} data row(s) for wave information processing.")
            template_structure = {
                "OlpnId": None
            }

            self.all_wave_information_payload = []
            for i, data_row in enumerate(list_of_datadict):
                row_num_in_sheet = i + 1
                logging.debug(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = data_row.get("Plant")
                environment = data_row.get("Environment")
                wave_id = str(data_row.get("Wave_number"))

                if not plant or not environment or not wave_id:
                    logging.error(f"INFO: Skipping row {row_num_in_sheet} due to missing Plant, Environment, or Wave_number.")
                    return []

                wave_id_split = wave_id.split(';')
                wave_id_query_value = "','".join(wave_id_split)

                payload = {
                    "Query": f"OrderPlanningRunId in ('{wave_id_query_value}') AND Status = '1000'",
                    "Template": template_structure
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
    # final_wave_information_payload = Wave_Information_Payload().extract_wave_olpn_information()
    # import json
    # print(json.dumps(final_wave_information_payload, indent=2))

    pack_olpn_payload = Wave_Information_Payload().extract_wave_olpn_information_for_pack_message()
    import json
    print(json.dumps(pack_olpn_payload, indent=4))

    # task_information = Wave_Information_Payload().extract_wave_task_detail_information()
    # import json
    # print(json.dumps(task_information, indent=4))

    # fc_olpn = Wave_Information_Payload().extract_wave_olpn_information_for_FC_packcomplete()
    # import json
    # print(json.dumps(fc_olpn, indent=4))