import logging
import json
import pandas as pd

from Inventory.Inventory_Payload_Generation.Inventory_WorkSheet_Extract import Inventory_WorkSheet_Extract

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Inventory_MHE_Journal_Payload:

    def __init__(self):
        self.inventory_worksheet = Inventory_WorkSheet_Extract()
        self.all_mhe_journal_payloads = []

    def create_inventory_mhe_journal_payloads(self) -> list:
        mhe_journal_data = self.inventory_worksheet.search_iLPN_parameters()

        if not mhe_journal_data:
            logging.info("No Valid MHE Journal parameters found, cannot create any payloads for MHE Journal task")
            return []

        for entry in mhe_journal_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            lpn_id = entry.get("iLPN_ID")

            message_type = ['DCI_DEI_AddConditionCode', 'Task_Update', 'RetrievalTaskResult', 'PPK_DEI_PickingFeedback',
                            'RoutingTaskResult', 'DCI_DEI_RemoveConditionCode', 'GoodsholderAnnounced',
                            'PTW_DEI_AllocationCreated', 'GoodsholderMeasured', 'PutawayTaskResult ',
                            'GoodsholderDivertedDueToException', ]

            lpn_id_string = str(lpn_id) if pd.notna(lpn_id) and lpn_id != '' else None

            if not all([plant, envn, message_type, lpn_id_string]):
                logging.info(f"Skipping entry due to missing data: {entry}")
                continue

            logging.info(f"Using LPNs from worksheet: '{lpn_id_string}'")
            lpn_list = [lpn.strip() for lpn in lpn_id_string.split(';')]

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
                          "FilterValues": lpn_list,
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
                    'MHEJournalPayload': mhe_journal_each_payload
                }

                self.all_mhe_journal_payloads.append(mhe_journal_payload)

        logging.info(f"Successfully created {len(self.all_mhe_journal_payloads)} "
                     f"payload generation(s) and sent to the program that called this function")

        return self.all_mhe_journal_payloads


if __name__ == "__main__":
    initiation = Inventory_MHE_Journal_Payload()
    payload = initiation.create_inventory_mhe_journal_payloads()
    for load in payload:
        print(json.dumps(load["MHEJournalPayload"], indent=2))