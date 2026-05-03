import logging
import json
import pandas as pd

from Inbound.Payload_generation.Worksheet_extract import Worksheet
from Inbound.Payload_generation.Get_LPN_List_From_ASN import lpn_list_from_asn

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IB_MHE_Journal_Payload:

    def __init__(self):
        self.worksheet = Worksheet()
        self.all_mhe_journal_payloads = []

    def create_mhe_journal_payloads(self) -> list:
        mhe_journal_data = self.worksheet.extract_mhe_journal_info()

        if not mhe_journal_data:
            logging.info("No Valid MHE Journal parameters found, cannot create any payloads for MHE Journal task")
            return []

        for entry in mhe_journal_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASN_ID")
            lpn_id = entry.get("LPN_ID")

            message_type = ['GoodsholderAnnounced', 'PTW_DEI_AllocationCreated', 'RoutingTaskResult',
                            'GoodsholderMeasured', 'PutawayTaskResult', 'DCI_DEI_RemoveConditionCode',
                            'GoodsholderDivertedDueToException']

            lpn_id_string = str(lpn_id) if pd.notna(lpn_id) and lpn_id != '' else None
            asn_id_string = str(asn_id) if pd.notna(asn_id) and asn_id != '' else None

            if not all([plant, envn, message_type, (asn_id_string or lpn_id_string)]):
                logging.info(f"Skipping entry due to missing data: {entry}")
                continue

            lpn_list = []
            if asn_id_string:
                logging.info(f"Found ASN(s) '{asn_id_string}'. Searching for associated LPNs...")
                search_task = []
                for single_asn in asn_id_string.split(';'):
                    single_asn = single_asn.strip()
                    param = {
                        'plant': plant,
                        'environment': envn,
                        'asn_ids': [single_asn.strip()]
                        }
                    search_task.append(param)

                if search_task:
                    asn_searcher = lpn_list_from_asn()
                    lpn_list_from_asn_search = asn_searcher.create_from_asn_list_of_lpn(search_task)
                    for lpn in lpn_list_from_asn_search:
                        lpn_list.extend(lpn)

            elif lpn_id_string:
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
    initiation = IB_MHE_Journal_Payload()
    payload = initiation.create_mhe_journal_payloads()
    for load in payload:
        print(json.dumps(load["MHEJournalPayload"], indent=2))