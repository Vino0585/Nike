import logging
import json
import pandas as pd

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet

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
            plant = str(entry.get("plant"))
            envn = str(entry.get("environment"))
            wave_number = str(entry.get("wave_number")) if pd.notna(entry.get("wave_number")) else None
            task_ids = str(entry.get("task_ids")) if pd.notna(entry.get("task_ids")) else None
            ilpns = str(entry.get("ilpns")) if pd.notna(entry.get("ilpns")) else None
            olpns = str(entry.get("olpns")) if pd.notna(entry.get("olpns")) else None
            order_ids = str(entry.get("order_ids")) if pd.notna(entry.get("order_ids")) else None

            message_type = ['PPK_DEI_TaskRelease', 'RetrievalTaskResult', 'PPK_DEI_PickingFeedback', 'PackTaskResult', 'Pack_Complete',
                            'RoutingTaskResult', 'GoodsholderDivertedDueToException', ]

            filter_values = []
            if wave_number:
                filter_values.append(f'"waveNumber":"{wave_number}"')
            if task_ids:
                filter_values.append(f'"taskId":"{task_ids}"')
            if ilpns:
                filter_values.append(f'"ilpn":"{ilpns}"')
            if olpns:
                filter_values.append(f'"olpn":"{olpns}"')
            if order_ids:
                filter_values.append(f'"orderId":"{order_ids}"')

            if not filter_values:
                logging.error("No values are given either in wavenbr or task or ilpn or olpn or order. Halting generation")
                return []

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
                    'filter_values': filter_values,
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