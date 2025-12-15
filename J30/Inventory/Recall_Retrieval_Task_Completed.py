import logging
import requests
from collections import defaultdict
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env

class Recall_Retrieval_Task_Payload():

   def create_recall_retrieval_task_payload(self):
       get_task_info_payload = Task_Search_Payload()
       raw_payload = get_task_info_payload.get_iLPN_information_worksheet()

        if not raw_payload:
           logging.error("No task information data found")
           return None

        payload_by_group = defaultdict(list)
        for package in raw_payload:
            if not isinstance(package, dict):
                logging.error(f"WARNING: Skipping package as it's not a valid dictionary: {package}")
                continue

            env = package.get('Environment')
            plant_id = package.get('Plant')
            payload = package.get('Payload')

            if env and plant_id and payload:
                payload_by_group[(env, plant_id)].append(payload)
            else:
                logging.error(f"WARNING: Skipping malformed package: {package}")

        env_handler = AWM_Env()

        response_result = []
        all_result_data = []
        for (environment, plant_id), payloads in payload_by_group.items():
            logging.info(f"Processing {len(payloads)} Payloads for Env: {environment.upper()} / Plant: {plant_id}")
            try:
                token_handler = Get_Token(env=environment.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                logging.info(f"Successfully retrieved token for {environment.upper()} env, Plant {plant_id}.")

                env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
                api_url = env_handler.get_program_url(program="Recall_Retrieval_Task_Complete")
                logging.info(f"Sending payloads to URL: {api_url}")

                header = {
                    "content-type": "application/json",
                    "selectedorganization": str(plant_id),
                    "selectedlocation": str(plant_id),
                    "authorization": f'Bearer {bearer_token}'
                }

                for i, payload_to_send in enumerate(payloads):
                    try:
                        logging.info(f"[{environment.upper()}] Processing Payload {i + 1}/{len(payloads)}")
                        response = requests.post(url=api_url, headers=header, json=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()
                        resp = response_data['data']['Results']
                        response_result.append(response_data.get('success'))
                        logging.info(f"SUCCESS: Payload {i + 1} processed successfully.")

                        for entry in resp:
                            pass

