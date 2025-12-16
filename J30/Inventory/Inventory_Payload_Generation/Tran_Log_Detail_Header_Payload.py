from Inventory.Inventory_Payload_Generation.Inventory_WorkSheet_Extract import Inventory_WorkSheet_Extract
import logging
import pandas as pd
import datetime as datetime
import json

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
        todays_date_str = datetime.date.today().strftime('%d %b %Y')
        yesterday_date_str = (datetime.date.today() - pd.Timedelta(days=1)).strftime('%d %b %Y')
        seven_days = (datetime.date.today() - pd.Timedelta(days=7)).strftime('%d %b %Y')

        for entry in self.all_search_iLPN_parameters:
            lpn_id = entry['iLPN_ID']
            message_type = entry['MESSAGE_TYPE']
            user_id = entry['USER_ID']
            date = entry['Date']


            if date == 'Today':
                msg_date = todays_date_str
            elif date == 'Yesterday':
                msg_date = yesterday_date_str
            elif date == '7':
                msg_date = seven_days
            else:
                msg_date = todays_date_str

            if pd.notna(lpn_id) and str(lpn_id).strip():
                lpn_id_list = str(lpn_id).split(';')
                for lpn in lpn_id_list:
                    lpn_id = lpn.strip()
                    if not lpn_id:
                        continue

                    # 1. Build the payload as a Python dictionary
                    payload_dict = {
                        "ViewName": "tranlogdetails",
                        "Filters": [
                            {
                                "ViewName": "tranlogdetails",
                                "AttributeId": "InternalProcessDate",
                                "Operator": "=",
                                "FilterValues": [
                                    {
                                        "filter": {
                                            "date": {
                                                "from": msg_date,
                                                "to": msg_date
                                            },
                                            "time": {
                                                "from": "00:00",
                                                "to": "23:59:59",
                                                "start": 0,
                                                "end": 288
                                            }
                                        }
                                    }
                                ]
                            },
                            {
                                "ViewName": "tranlogdetails",
                                "AttributeId": "MsgType",
                                "Operator": "=",
                                "FilterValues": [message_type]
                            },
                            {
                                "ViewName": "tranlogdetails",
                                "AttributeId": "Direction",
                                "DataType": "date",
                                "Operator": "=",
                                "FilterValues": ["Outbound"]
                            },
                            {
                                "ViewName": "tranlogdetails",
                                "AttributeId": "TextSearch",
                                "Operator": "=",
                                "FilterValues": [lpn_id]
                            }
                        ],
                        "Page": 0,
                        "TotalCount": -1,
                        "SortOrder": "desc",
                        "SortIndicator": "chevron-up",
                        "TimeZone": "Japan",
                        "EnableMaxCountLimit": True,
                        "MaxCountLimit": 500,
                        "ComponentName": "com-manh-cp-xint",
                        "Size": 25,
                        "Sort": "InternalProcessDate"
                    }

                    # 2. Serialize the dictionary to a compact JSON string
                    final_payload = json.dumps(payload_dict)

                    all_payloads.append({
                        "Environment": entry.get("Environment"),
                        "Plant": entry.get("Plant"),
                        "Tran_log_detail_payload": final_payload
                    })

            return all_payloads

if __name__ == '__main__':
    py = Tran_log_detail_header()
    full_payload = py.construct_tran_log_detail_header_payload()
    for payload in full_payload:
        print(payload.get('tran_log_detail_payload'))
