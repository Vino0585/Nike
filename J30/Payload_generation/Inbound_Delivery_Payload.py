# This program will not follow other program way of creation but will also add get inbound delivery payload and construct the add asn to inbound delivery to payload return it.

from Environment.Get_Token import Get_Token
from Worksheet_extract import Worksheet
from Environment.WM_Environment import AWM_Env

class Inbound_Delivery_Payload:

    def __init__(self):
        self.inbound_delivery_id = ''
        self.worksheet = Worksheet()
        self.all_parse_parameter = []

    def parse_inbound_worksheet(self):
        get_ib_data = self.worksheet.inbound_delivery_worksheet_extract()
        if not get_ib_data:
            print('Worksheet extract didnt return any information')
            return []

        for entry in get_ib_data:
            plant = entry.get("Plant")
            environment = entry.get("Environment")
            asn_ids = entry.get("ASNID")

            params = {
                'Plant': plant,
                'Environment': environment,
                'ASNID': asn_ids
            }
            self.all_parse_parameter.append(params)


    def create_and_get_inbound_delivery_id(self):

        bearer_token = ''
        for entry in self.all_parse_parameter:
            environment = entry.get("Environment")
            plant_id = entry.get("Plant")
            token_handler = Get_Token(env=environment.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()

            env_handler = AWM_Env()
            # Get URL ONCE for this group
            env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
            # Hardcode the program name for reliability, fixing the issue where it resolves incorrectly.
            api_url = env_handler.get_program_url(program="Putaway_Task_Complete")
            print(f"Sending payloads to URL: {api_url}")

            headers = {
                "content-type": "application/json",
                "selectedorganization": str(plant_id),
                "selectedlocation": str(plant_id),
                "authorization": f'Bearer {bearer_token}'
            }

