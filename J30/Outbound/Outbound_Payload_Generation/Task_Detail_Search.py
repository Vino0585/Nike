import logging
import requests

from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Task_Search_Payload:

    def __init__(self):
        self.search_by_ilpn = ''
        self.search_by_orderid = ''
        self.template_structure = {"TaskId": None, "ItemId": None, "SourceContainerId": None, "SourceLocationId": None,
                                   "GenerationCodeId": None, "GenerationNumberId": None, "TypeId": None, "Status": None,
                                   "TargetLocationId": None, "TargetContainerId": None, "OrderId": None, "CriteriaId": None,
                                   "OriginalOrderId": None, "Quantity": None, "OrderCriteriaId": None, "OlpnId": None,
                                   "ShipmentId": None}
        self.bearer_token = ''
        self.all_task_search_list = []

    # Task Detail status codes: 1000 is created; 8000 is Completed; 9000 is canceled.


    def get_bearer_token(self, environment, plant_id):
        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()
        return bearer_token

    def get_task_detail_api_response(self, bearer_token, environment, plant_id, payload):
        env_handler = AWM_OB_Env()
        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
        url_value = env_handler.get_program_url(program="Search_Task_Detail")
        logging.info(f"Sending payload to URL: {url_value}")

        headers = {
            "content-type": "application/json",
            "organization": str(plant_id),
            "location": str(plant_id),
            "authorization": 'Bearer ' + bearer_token
        }

        response = requests.post(url=url_value, headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()
        response_result = response_data['data']

        if response_result is True:
            logging.info(
                "Task information search for the iLPN is complete and successfully sent to the program that called this function")
        else:
            logging.info(
                f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")

        return response_result

    def search_task_detail_fullcase_payloads_by_ilpns(self, search_by_ilpns, environment, plant_id):
        self.search_by_ilpn = ",".join(search_by_ilpns.split(';'))

        if not self.search_by_ilpn:
            logging.info("No valid search by iLPN found, cannot create any payloads, check self.search_by_iLPN in task_search_payload")

        bearer_token = self.get_bearer_token(environment, plant_id)

        payload = {
            "Query": f"SourceContainerId in ({self.search_by_ilpn}) AND TypeId = 'PICK/PACK' "
                     f"AND GenerationCodeId in ('Wave', 'Stream')",
            "Template": self.template_structure
        }

        get_response = self.get_task_detail_api_response(bearer_token, environment, plant_id, payload)

        iLPN_list = []
        oLPN_list = []

        for i, item in enumerate(get_response):
            ilpn = get_response[i]['SourceContainerId'] # This is the iLPN
            olpn = get_response[i]['OlpnId'] # This is the oLPN

            iLPN_list.append(ilpn)
            oLPN_list.append(olpn)

        data = {
            "iLPN": iLPN_list,
            "oLPN": oLPN_list
        }

        return data

    def search_task_detail_fullcase_payloads_by_ilpns_for_mhe_journal(self, search_by_ilpns, environment, plant_id):
        self.search_by_ilpn = ",".join(search_by_ilpns.split(';'))

        if not self.search_by_ilpn:
            logging.info("No valid search by iLPN found, cannot create any payloads, check self.search_by_iLPN in task_search_payload")

        bearer_token = self.get_bearer_token(environment, plant_id)

        template = {}
        payload = {
            "Query": f"SourceContainerId in ({self.search_by_ilpn}) AND TypeId = 'PICK/PACK' "
                     f"AND GenerationCodeId in ('Wave', 'Stream')",
            "Template": self.template_structure
        }

        get_response = self.get_task_detail_api_response(bearer_token, environment, plant_id, payload)
        iLPN_list = []
        oLPN_list = []

        for i, item in enumerate(get_response):
            ilpn = get_response[i]['SourceContainerId'] # This is the iLPN
            olpn = get_response[i]['OlpnId'] # This is the oLPN

            iLPN_list.append(ilpn)
            oLPN_list.append(olpn)

        data = {
            "iLPN": iLPN_list,
            "oLPN": oLPN_list
        }

        return data

    def search_task_detail_fullcase_payloads_by_order(self, order_id, environment, plant_id):
        self.search_by_orderid = ",".join(order_id.split(';'))

        if not self.search_by_orderid:
            logging.info("No valid search by Order found, cannot create any payloads, check self.search_by_orderid in task_search_payload")

        bearer_token = self.get_bearer_token(environment, plant_id)

        payload = {
            "Query": f"OriginalOrderId in ({self.search_by_orderid})",
            "Template": self.template_structure
        }

        get_response = self.get_task_detail_api_response(bearer_token, environment, plant_id, payload)
        iLPN_list = []
        oLPN_list = []

        for i, item in enumerate(get_response):
            ilpn = get_response[i]['SourceContainerId'] # This is the iLPN
            olpn = get_response[i]['OlpnId'] # This is the oLPN

            iLPN_list.append(ilpn)
            oLPN_list.append(olpn)

        data = {
            "iLPN": iLPN_list,
            "oLPN": oLPN_list
        }

        return data


if __name__ == "__main__":
    task_search = Task_Search_Payload()
    iLPN = '00000010810000000549;00081012220267664105'
    generated_payloads = task_search.search_task_detail_fullcase_payloads_by_ilpns(iLPN, 'qa', '1081')
    # Pretty-logging.info the result for better readability
    import json
    logging.info(json.dumps(generated_payloads, indent=2))