import logging
import json
import pandas as pd

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Outbound.Outbound_Payload_Generation.Task_Detail_Search import Task_Search_Payload

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


class Outbound_MHE_Journal_Payload:

    def __init__(self):
        self.task_search = Task_Search_Payload()
        self.all_mhe_journal_payloads = []

    def create_outbound_mhe_journal_payloads(self) -> list:
        mhe_journal_data = self.task_search.search_task_detail_worksheet_info()

        if not mhe_journal_data:
            logging.info("No Valid MHE Journal parameters found, cannot create any payloads for MHE Journal task")
            return []

        plant = mhe_journal_data[0]['Plant']
        envn = mhe_journal_data[0]['Environment']

        for each_iLPN in mhe_journal_data[0].get('iLPN', []):
            if len(each_iLPN) != 20:
                logging.warning(f"iLPN '{each_iLPN}' is not 20 characters long and will be skipped.")
                continue

            message_types = ['PPK_DEI_TaskRelease', 'RetrievalTaskResult', 'RoutingTaskResult', 'PTW_DEI_AllocationCreated ',
                             'ReplenTaskResult ', 'GoodsholderDivertedDueToException']

            # 'PackTaskResult', 'Pack_Complete',
            for message in message_types:
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
                          "FilterValues": [each_iLPN],
                          "negativeFilter": False
                        }
                      ],
                      "TimeZone": "Japan",
                      "ComponentName": "com-manh-cp-dmui-search"
                }

                mhe_journal_payload = {
                    'environment': envn,
                    'plant': plant,
                    'MHEJournalPayload': mhe_journal_each_payload
                }

                self.all_mhe_journal_payloads.append(mhe_journal_payload)



        logging.info(f"Successfully created {len(self.all_mhe_journal_payloads)} "
                     f"payload generation(s) and sent to the program that called this function")

        return self.all_mhe_journal_payloads


if __name__ == "__main__":
    initiation = Outbound_MHE_Journal_Payload()
    payload = initiation.create_outbound_mhe_journal_payloads()
    for load in payload:
        print(json.dumps(load["MHEJournalPayload"], indent=2))