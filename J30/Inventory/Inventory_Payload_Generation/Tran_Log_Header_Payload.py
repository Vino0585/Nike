# I want to create a payload structure of this type:
#
# {
#    "ViewName":"tranlogdetails",
#    "Filters":[
#       {
#          "ViewName":"tranlogdetails",
#          "AttributeId":"InternalProcessDate",
#          "Operator":"=",
#          "FilterValues":[
#             {
#                "filter":{
#                   "date":{
#                      "from":"15 Dec 2025",
#                      "to":"15 Dec 2025"
#                   },
#                   "time":{
#                      "from":"00:00",
#                      "to":"23:59:59",
#                      "start":0,
#                      "end":288
#                   }
#                }
#             }
#          ]
#       },
#       {
#          "ViewName":"tranlogdetails",
#          "AttributeId":"MsgType",
#          "Operator":"=",
#          "FilterValues":[
#             "PIX_XIN_InventoryAdjustment"
#          ]
#       },
#       {
#          "ViewName":"tranlogdetails",
#          "AttributeId":"Direction",
#          "DataType":"date",
#          "Operator":"=",
#          "FilterValues":[
#             "Outbound"
#          ]
#       },
#       {
#          "ViewName":"tranlogdetails",
#          "AttributeId":"TextSearch",
#          "Operator":"=",
#          "FilterValues":[
#             "vgana3"
#          ]
#       }
#    ],
#    "Page":0,
#    "TotalCount":-1,
#    "SortOrder":"desc",
#    "SortIndicator":"chevron-up",
#    "TimeZone":"Japan",
#    "EnableMaxCountLimit":true,
#    "MaxCountLimit":500,
#    "ComponentName":"com-manh-cp-xint",
#    "Size":25,
#    "Sort":"InternalProcessDate"
# }

from Inventory.Inventory_Payload_Generation.Inventory_WorkSheet_Extract import Inventory_WorkSheet_Extract
import logging
import pandas as pd
from datetime import date

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Tran_log_detail_header:
    
    def __init__(self):
        self.inventory_worksheet = Inventory_WorkSheet_Extract()
        self.all_iLPN_search_payload = []
        self.all_search_iLPN_parameters = self.inventory_worksheet.search_iLPN_parameters()
        
    def construct_tran_log_detail_header_payload(self):
        if not self.all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        # Get today's date and format it to 'DD Mon YYYY' (e.g., '26 Oct 2023')
        todays_date_str = date.today().strftime('%d %b %Y')

        for entry in self.all_search_iLPN_parameters:
            lpn_id = entry['iLPN_ID']
            message_type = entry['MESSAGE_TYPE']
            user_id = entry['USER_ID']

            if pd.notna(lpn_id) and str(lpn_id).strip():
                lpn_id_list = str(lpn_id).split(';')
                for lpn in lpn_id_list:
                    lpn_id = lpn.strip()
                    if not lpn_id:
                        continue

                    # 1. Construct individual filter components as strings
                    date_filter = f"""{{
                        "ViewName": "tranlogdetails",
                        "AttributeId": "InternalProcessDate",
                        "Operator": "=",
                        "FilterValues": [
                            {{
                                "filter": {{
                                    "date": {{
                                        "from": "{todays_date_str}",
                                        "to": "{todays_date_str}"
                                    }},
                                    "time": {{
                                        "from": "00:00",
                                        "to": "23:59:59",
                                        "start": 0,
                                        "end": 288
                                    }}
                                }}
                            }}
                        ]
                    }}"""
                    
                    msg_type_filter = f"""{{
                        "ViewName": "tranlogdetails",
                        "AttributeId": "MsgType",
                        "Operator": "=",
                        "FilterValues": [
                            "{message_type}"
                        ]
                    }}"""

                    # Let's assume 'direction' is a variable holding the value you want.
                    direction = "Outbound"
                    direction_filter = f"""{{
                        "ViewName": "tranlogdetails",
                        "AttributeId": "Direction",
                        "DataType": "date",
                        "Operator": "=",
                        "FilterValues": [
                            "{direction}"
                        ]
                    }}"""

                    text_search_filter = f"""{{
                        "ViewName": "tranlogdetails",
                        "AttributeId": "TextSearch",
                        "Operator": "=",
                        "FilterValues": [
                            f"{user_id}"
                        ]
                    }}"""
                    
                    # Define the static footer part of the payload for reusability
                    payload_footer = f""""Page": 0,
                        "TotalCount": -1,
                        "SortOrder": "desc",
                        "SortIndicator": "chevron-up",
                        "TimeZone": "Japan",
                        "EnableMaxCountLimit": true,
                        "MaxCountLimit": 500,
                        "ComponentName": "com-manh-cp-xint",
                        "Size": 25,
                        "Sort": "InternalProcessDate"
                    """

                    # 2. Assemble the final payload using the filter strings
                    final_payload = f"""{{
                        "ViewName": "tranlogdetails",
                        "Filters": [
                            {date_filter},
                            {msg_type_filter},
                            {direction_filter},
                            {text_search_filter}
                        ],
                        {payload_footer}
                    }}"""

                    all_payloads.append({
                        "envn": entry.get("Environment"),
                        "plant": entry.get("Plant"),
                        "tran_log_detail_payload": final_payload
                    })

            return all_payloads

if __name__ == '__main__':
    py = Tran_log_detail_header()
    full_payload = py.construct_tran_log_detail_header_payload()
    for payload in full_payload:
        print(payload.get('tran_log_detail_payload'))
