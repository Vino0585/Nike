import logging
import json
import pandas as pd

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Outbound.Outbound_Payload_Generation.Task_Detail_Search
from Outbound.Outbound_Payload_Generation.Task_Detail_Search import Task_Search_Payload

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Outbound_MHE_Journal_Payload:

    def __init__(self):
        self.outbound_worksheet = Outbound_Worksheet()
        self.all_mhe_journal_payloads = []

    def create_outbound_mhe_journal_payloads(self) -> list:
        mhe_journal_data = self.outbound_worksheet.mhe_journal_worksheet_extract_parameter()

        if not mhe_journal_data:
            logging.info("No Valid MHE Journal parameters found, cannot create any payloads for MHE Journal task")
            return []

        for entry in mhe_journal_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            wave_number = entry.get("WaveNumber")
            task_ids = entry.get("task_ids")
            ilpns = entry.get("ilpns")
            olpns = entry.get("olpns")
            order_ids = entry.get("order_ids")

            message_type = ['PPK_DEI_TaskRelease', 'RetrievalTaskResult', 'PPK_DEI_PickingFeedback', 'PackTaskResult', 'Pack_Complete',
                            'RoutingTaskResult', 'GoodsholderDivertedDueToException', ]

            wave_number_string = str(wave_number) if pd.notna(wave_number) and wave_number != '' else None
            task_id_string = str(order_id) if pd.notna(order_id) and order_id != '' else None
            task_id_string = str(task_ids) if pd.notna(task_ids) and task_ids != '' else None
            ilpn_string = str(ilpns) if pd.notna(ilpns) and ilpns != '' else None
            olpn_string = str(olpns) if pd.notna(olpns) and olpns != '' else None
            order_id_string = str(order_ids) if pd.notna(order_ids) and order_ids != '' else None

            if wave_number_string != None:
              wave_number_list = wave_number_string.split(';')
            elif task_id_string != None:
              task_id_list = task_id_string.split(';')
            elif ilpn_string != None:
              ilpn_list = ilpn_string.split(';')
            elif olpn_string != None:
              olpn_list = olpn_string.split(';')
            else:
              order_id_list = order_id_string.split(';')
            filter_values = []
            if wave_number_string:
                filter_values = wave_number_string.split(';')
            elif task_id_string:
                filter_values = task_id_string.split(';')
            elif ilpn_string:
                filter_values = ilpn_string.split(';')
            elif olpn_string:
                filter_values = olpn_string.split(';')
            elif order_id_string:
                filter_values = order_id_string.split(';')

            filter_values = None
            if ilpn_list:
              filter_values = ilpn_list
            elif olpn_list:
              filter_values = olpn_list
            elif task_id_list:
              filter_values = task_id_list
            elif order_id_list:
              
            
            
            if not filter_values:
                continue


            for message in message_type:
                mhe_journal_each_payload = {
                      "ViewName": "MessageJournal",
                      "Filters": [
                        {
                          "AttributeId": "MessageType",
                          "FilterValues": [
                            message
                          ]
                        },
                        {
                          "AttributeId": "Stage1.MessagePayload",
                          "FilterValues": filter_values,
                          "negativeFilter": False
                        }
                      ],
                      "TimeZone": "Japan",
                      "ComponentName": "com-manh-cp-dmui-search"
                    }

                mhe_journal_payload = {
                    'environment': envn,
                    'plant': plant,
                    'lpn_list': lpn_list,
                    'lpn_list': filter_values,
                    'MHEJournalPayload': mhe_journal_each_payload
                }

                self.all_mhe_journal_payloads.append(mhe_journal_payload)

        logging.info(f"Successfully created {len(self.all_mhe_journal_payloads)} "
                     f"payload generation(s) and sent to the program that called this function")

        return self.all_mhe_journal_payloads


if __name__ == "__main__":
    initiation = Inventory_MHE_Journal_Payload()
    payload = initiation.create_inventory_mhe_journal_payloads()
    initiation = Outbound_MHE_Journal_Payload()
    payload = initiation.create_outbound_mhe_journal_payloads()
    for load in payload:
        print(json.dumps(load["MHEJournalPayload"], indent=2))