import uuid
import datetime as dt
import logging
import json

from Payload_generation.Worksheet_extract import Worksheet

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Routing_Task_Completed_Payload:

    def __init__(self):
        self.worksheet = Worksheet()
        self.all_routing_task_completed = []

    def create_routing_task_completed_payloads(self) -> list:
        routing_task_data = self.worksheet.get_lpn_for_routing_task_complete()

        if not routing_task_data:
            logging.info("No valid routing task parameters found, cannot create any payloads.")
            return []

        for entry in routing_task_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            lpn_id = entry.get("LPN_ID")
            diversion_code = entry.get("Diversion_Code")
            aware_timestamp = dt.datetime.now(dt.timezone.utc)
            iso_timestamp_str = aware_timestamp.isoformat()
            event_id = str(uuid.uuid4())
            routing_each_payload = {}

            if not all([plant, envn, lpn_id, diversion_code]):
                logging.error(f"Skipping entry due to missing data {entry}")
                continue

            locn = ''
            if diversion_code == 'FirstSKU':
                locn = '15030000000'
            elif diversion_code == 'MultiSKU':
                locn = '15030000000'
            elif diversion_code == 'InVas':
                locn = '1504000000'
            elif diversion_code == 'QA':
                locn = '1502000000'
            elif diversion_code == 'Measure':
                locn = '1505000000'

            if diversion_code != 'STORAGE':
                routing_each_payload = {
                    "event": {
                        "type": "ROUTING_TASK_COMPLETED",
                        "tmst": iso_timestamp_str,
                        "timezone": "UTC+09:00",
                        "id": event_id,
                        "correlationId": None,
                        "distributionCenterCd": f"NODE_{plant}",
                        "technicalSolutionSourceCd": "NAS_V001",
                        "version": "1.0.0"
                    },
                    "data": {
                        "distributionCenterCd": f"NODE_{plant}",
                        "taskId": f"IBPW0000000351",
                        "goodsholderId": f"{lpn_id}",
                        "executionTmst": iso_timestamp_str,
                        "routingTaskCompleted": {
                            "routedToDestinationLocationId": f"{locn}"
                        }
                    }
                }

                routing_payload = {
                    'environment': envn,
                    'plant': plant,
                    'RoutingPayload': routing_each_payload
                }
                self.all_routing_task_completed.append(routing_payload)

        logging.info(f"Successfully created {len(self.all_routing_task_completed)} payload generation(s) "
                     f"and sent to the program that called this function")

        return self.all_routing_task_completed

initiation = Routing_Task_Completed_Payload()
payload = initiation.create_routing_task_completed_payloads()
for load in payload:
    print(json.dumps(load, indent=2))