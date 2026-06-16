import logging
from pathlib import Path
import sys
import uuid
import datetime

# Ensure the J30 project root is on sys.path so the `Outbound` package can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Wave_Information import Wave_Information_Search

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Pack_Complete_Payload:
    def __init__(self):
        self.all_wave_information_payload = []
        self.wave_information = Wave_Information_Search()
        self.olpn_search_payload = self.wave_information.search_olpn_payload_for_pack_complete()
        self.all_pack_complete_payload = []

    def pack_complete_payload(self):
        if not self.olpn_search_payload:
            logging.error("No payload returned from Wave Information for pack complete payload creation")

        plant = self.olpn_search_payload['Plant']
        env = self.olpn_search_payload['Env']
        payloads = self.olpn_search_payload['Result']
        now = datetime.datetime.today()
        event_identifier = f"{plant}_{now.strftime('%Y%m%d')}-{uuid.uuid4()}"
        event_time_stamp = now.isoformat(timespec='seconds')
        pack_complete_payload = []
        for i, payload in enumerate(payloads):
            pack_complete_payload_created = {
                    "nodeAPI": {
                        "sourceSystemName": "NODE_PACK_AUDIT_AND_VAS_1081", "eventTypeCode": "PACKGOODSHOLDER",
                        "eventIdentifier": event_identifier, "eventTimestamp": event_time_stamp,
                        "eventTimeZoneCode": "UTC+09:00",
                        "businessKeyStructureText": "distributionCenterCd|transportgoodsholderId",
                        "businessKeyValueText": f"{plant}|{payload['OlpnId']}",
                        "packGoodsHolderRequest": {
                            "distributionCenterCd": str(plant), "nodeDistributionOrderId": str(payload['AggregatedOrder']),
                            "transportGoodsHolderId": str(payload['OlpnId']),
                            "laborActivityId": "", "transactionId": "", "containerTypeId": "", "criteriaID": "",
                            "items": [
                                    {
                                    "productCode": str(payload['Item']),
                                    "countryOfOrigin": None,
                                    "quantity": int(payload['Qty']),
                                    "shortedQuantity": 0
                                    }
                                    ]
                                }
                            }
                        }
            pack_complete_payload.append(pack_complete_payload_created)

        self.all_pack_complete_payload = {
            'Plant': plant, 'Env': env, 'Payloads': pack_complete_payload
        }
        return self.all_pack_complete_payload


if __name__ == '__main__':
    pack_olpns = Pack_Complete_Payload().pack_complete_payload()
    print(pack_olpns)