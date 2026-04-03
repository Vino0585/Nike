from math import isnan

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
import logging
import pandas as pd
import datetime as datetime
import json

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Tran_log_detail_header:
    
    def __init__(self):
        self.outbound_worksheet = Outbound_Worksheet()
        self.all_tran_log_header_search_payload = []
        self.all_search_tran_log_parameters = self.outbound_worksheet.tran_log_worksheet_extract_parameter()
        
    def construct_tran_log_detail_header_payload(self):
        if not self.all_search_tran_log_parameters:
            logging.error("No valid information are there in worksheet check your worksheet.")
            return []

        all_payloads = []
        # Get today's date and format it to 'DD Mon YYYY' (e.g., '26 Oct 2023')
        todays_date_str = datetime.date.today().strftime('%d %b %Y')
        yesterday_date_str = (datetime.date.today() - pd.Timedelta(days=1)).strftime('%d %b %Y')
        seven_days = (datetime.date.today() - pd.Timedelta(days=7)).strftime('%d %b %Y')
        tomorrow_date_str = (datetime.date.today() + pd.Timedelta(days=1)).strftime('%d %b %Y')

        # With order the msg_type is as following
        order_msg_type = ['XNT_DCO_MANIKEImportOrigOrder', 'DCO_XNT_NIKEINT10MAWMOODROP', 'XNT_DCO_MANIKEUPDATEORDER',
                    'PPK_XIN_NIKEINT06V2ShipCreate', 'SHP_XNT_NIKEINT07TrailerLoadedMsg', 'SHC_ANY_NIKEShipConfirm']

        # With LPN the msg_type is as following
        lpn_msg_type = ['XNT_PPK_NIKELBL00GPSLABELCALLBACK']

        for entry in self.all_search_iLPN_parameters:
            lpn_id = entry['iLPN_ID']
            message_type = entry['MESSAGE_TYPE']
            user_id = entry['USER_ID']
            date = entry['Date']

            if lpn_id is None:
                lpn_id = user_id


            if date == 'Today':
                msg_date = todays_date_str
            elif date == 'Yesterday':
                msg_date = yesterday_date_str
            elif date == 'Tomorrow':
                msg_date = tomorrow_date_str
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
                                                "to": todays_date_str
                                            },
                                            "time": {
                                                "from": "00:00:00",
                                                "to": "23:59:59",
                                                # "start": 0,
                                                # "end": 288
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
                            # {
                            #     "ViewName": "tranlogdetails",
                            #     "AttributeId": "Direction",
                            #     "DataType": "date",
                            #     "Operator": "=",
                            #     "FilterValues": ["Outbound"]
                            # },
                            {
                                "ViewName": "tranlogdetails",
                                "AttributeId": "TextSearch",
                                "Operator": "=",
                                "FilterValues": lpn_id
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
    full_payload_tran_header = py.construct_tran_log_detail_header_payload()
    from pprint import pprint
    for payload in full_payload_tran_header:
        pprint(payload.get('Tran_log_detail_payload'))
