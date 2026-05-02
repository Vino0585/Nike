import requests
import logging
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
import pandas as pd
from Inventory.Inventory_Payload_Generation.Inventory_WorkSheet_Extract import Inventory_WorkSheet_Extract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Task_Search_Payload:

    def __init__(self):
        self.search_by_ilpn = ''
        self.worksheet = Inventory_WorkSheet_Extract()
        self.all_lpn_information_payload = []

    def search_task_detail_payloads(self, search_by_ilpns, environment, plant_id):
        self.search_by_ilpn = ",".join(search_by_ilpns.split(';'))

        if not self.search_by_ilpn:
            print("No valid search by iLPN found, cannot create any payloads, check self.search_by_iLPN in task_search_payload")

        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()

        template_structure = {"TaskId": None, "SourceContainerId": None, "ItemId": None, "SourceLocationId": None}
        payload = {
            "Query": f"SourceContainerId in ({self.search_by_ilpn}) AND GenerationCodeId = 'Recall' AND TypeId = 'REPLENISHMENT'",
            "Template": template_structure
        }

        env_handler = AWM_Env()
        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
        url_value = env_handler.get_program_url(program="Search_Task_Detail")
        print(f"Sending payload to URL: {url_value}")

        headers = {
            "content-type": "application/json",
            "organization": str(plant_id),
            "location": str(plant_id),
            "authorization": 'Bearer ' + bearer_token
        }

        response = requests.post(url=url_value, headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()
        response_result = response_data.get('success')

        if response_result is True:
            print("Task information search for the iLPN is complete and successfully sent to the program that called this function")
        else:
            print(f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")

        return response_data

    def get_iLPN_information_worksheet(self):
        lpn_information_data = self.worksheet.search_recall_iLPN_parameters()

        if not lpn_information_data:
            logging.info(
                "No Valid LPN Information parameter found, cannot create any payloads for LPN Information task")
            return []

        for entry in lpn_information_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            lpn_id_raw = entry.get("iLPN_ID")

            lpn_id_string = str(lpn_id_raw) if pd.notna(lpn_id_raw) and lpn_id_raw != '' else None

            if not all([plant, envn, lpn_id_string]):
                logging.info(f"Skipping entry due to missing data: {entry}")
                continue

            generated_payloads = task_search.search_task_detail_payloads(lpn_id_string, envn, plant)

            final_payload = {
                'Plant': plant,
                'Environment': envn,
                'Payload': generated_payloads['data']
            }

            return final_payload


if __name__ == "__main__":
    task_search = Task_Search_Payload()
    # iLPN = '20251202122224000001'
    # generated_payloads = task_search.search_task_detail_payloads(iLPN, 'qa', '1081')
    # Pretty-print the result for better readability
    generated_payload = task_search.get_iLPN_information_worksheet()
    import json
    print(json.dumps(generated_payload, indent=4))