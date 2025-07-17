import requests
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env


class Task_Search_Payload:

    def __init__(self):
        self.search_by_ilpn = ''
        all_task_search_list = []

    def search_task_detail_payloads(self, search_by_ilpns, environment, plant_id):
        self.search_by_ilpn = ",".join(search_by_ilpns.split(';'))

        if not self.search_by_ilpn:
            print("No valid search by iLPN found, cannot create any payloads, check self.search_by_iLPN in task_search_payload")

        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()

        template_structure = {"TaskId": None, "SourceContainerId": None, "ItemId": None, "TargetLocationId": None}
        payload = {
            "Query": f"SourceContainerId in ({self.search_by_ilpn})",
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
        print(f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")

        return response_data

# if __name__ == "__main__":
#     task_search = Task_Search_Payload()
#     iLPN = '0000VG16072025QA71880000;00000000108101023408'
#     generated_payloads = task_search.search_task_detail_payloads(iLPN, 'qa', '1081')
#     # Pretty-print the result for better readability
#     import json
#     print(json.dumps(generated_payloads, indent=2))