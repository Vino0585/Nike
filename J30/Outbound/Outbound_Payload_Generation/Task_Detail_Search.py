import logging
import requests

from Environment.Get_Token import Get_Token
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env
from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Outbound.Order_Search import Outbound_Order_Search

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
        self.worksheet = Outbound_Worksheet()
        self.order_search = Outbound_Order_Search()


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

        payload = payload
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

    def search_task_detail_by_lpns(self, search_by_ilpns, environment, plant_id):
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
            "Plant": plant_id,
            "Environment": environment,
            "iLPN": iLPN_list,
            "oLPN": oLPN_list
        }

        return data

    def search_task_detail_by_wave_nbr(self, search_by_wave_nbr, environment, plant_id):
        self.search_by_wavenbr = ",".join(search_by_wave_nbr.split(';'))

        if not self.search_by_wavenbr:
            logging.info("No valid search by iLPN found, cannot create any payloads, check self.search_by_iLPN in task_search_payload")

        bearer_token = self.get_bearer_token(environment, plant_id)

        template = {}
        payload = {
            "Query": f"GenerationNumberId in ({self.search_by_wavenbr})"
                     f"AND GenerationCodeId in ('Wave', 'Stream')"
                     f"AND Status in ('1000', '8000')",
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
            "Plant": plant_id,
            "Environment": environment,
            "iLPN": iLPN_list,
            "oLPN": oLPN_list
        }

        return data


    def search_task_detail_by_order(self, order_id, environment, plant_id):
        self.search_by_orderid = ",".join(order_id[0].split(';'))

        if not self.search_by_orderid:
            logging.info("No valid search by Order found, cannot create any payloads, check self.search_by_orderid in task_search_payload")

        bearer_token = self.get_bearer_token(environment, plant_id)
        env = environment
        plant = plant_id
        payload = {
            "Query": f"OrderId in ({self.search_by_orderid})"
        }

        get_response = self.get_task_detail_api_response(bearer_token=bearer_token, environment=env, plant_id=plant, payload=payload)
        iLPN_list = []
        oLPN_list = []

        for i, item in enumerate(get_response):
            olpn = get_response[i]['OlpnId'] # This is the oLPN
            oLPN_list.append(olpn)

        data = {
            "Plant": plant_id,
            "Environment": environment,
            "oLPN": oLPN_list
        }

        return data

    def search_task_detail_worksheet_info(self):
        try:
            worksheet_info = self.worksheet.mhe_journal_worksheet_extract_parameter()
            if not worksheet_info:
                logging.info("No Worksheet information is provided in mhe_journal_worksheet_extract_parameter in Outbound_Worksheet_Extract.py")
                return []
            logging.info(f"Successfully extracted {len(worksheet_info)} data row(s) for search order processing")

            self.all_task_search_list = []
            for i, data_row in enumerate(worksheet_info):
                row_num_in_sheet = i + 1
                logging.info(f"Processing row {row_num_in_sheet}: {data_row}")

                plant = str(data_row.get("Plant"))
                environment = data_row.get("Environment")
                order_ids = data_row.get("Order_ids")
                wave_number = data_row.get("Wave_number")
                task_id = data_row.get("Task_ids")
                ilpns = data_row.get("iLPNs")
                olpns = data_row.get("oLPNs")

                if order_ids and str(order_ids).lower() != 'nan' and order_ids != '0000000nan':
                    parent_order_line_id = self.order_search.mhe_search_parent_order_payload(plant, environment, order_ids)
                    plant = parent_order_line_id['Plant']
                    environment = parent_order_line_id['Environment']
                    order_ids = parent_order_line_id['OrderId']
                    get_result = self.search_task_detail_by_order(order_ids, environment, plant)
                    self.all_task_search_list.append(get_result)
                    print(get_result)
                elif ilpns and str(ilpns).lower() != 'nan':
                    get_result = self.search_task_detail_by_lpns(ilpns, environment, plant)
                    self.all_task_search_list.append(get_result)
                    print(get_result)
                elif olpns and str(olpns).lower() != 'nan':
                    get_result = self.search_task_detail_by_lpns(olpns, environment, plant)
                    self.all_task_search_list.append(get_result)
                    print(get_result)
                elif wave_number and str(wave_number).lower() != 'nan':
                    get_result = self.search_task_detail_by_wave_nbr(plant_id=plant, environment=environment, search_by_wave_nbr=wave_number)
                    self.all_task_search_list.append(get_result)
                    print(get_result)
                else:
                    logging.info(f"We have not coded other search process will work on it and get "
                                 f"back so use by order or ilpn or olpn for now")

            return self.all_task_search_list

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")



if __name__ == "__main__":
    task_search = Task_Search_Payload()
    # iLPN = '00000010810000000549;00081012220267664105'
    # generated_payloads = task_search.search_task_detail_fullcase_payloads_by_ilpns(iLPN, 'qa', '1081')
    # # Pretty-logging.info the result for better readability
    # import json
    # logging.info(json.dumps(generated_payloads, indent=2))
    generated_payloads = task_search.search_task_detail_worksheet_info()