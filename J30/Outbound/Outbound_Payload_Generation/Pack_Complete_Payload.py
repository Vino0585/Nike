import logging
from pathlib import Path
import sys
import uuid
import datetime
import json
from collections import defaultdict

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

    @staticmethod
    def _normalize_item_row(payload):
        if not isinstance(payload, dict):
            return None

        olpn_id = payload.get("OlpnId")
        item_id = payload.get("ItemId")
        qty = payload.get("InitialQuantity")
        order_id = payload.get("OrderId")

        if not (olpn_id and item_id and order_id):
            return None

        try:
            qty = int(qty)
        except (TypeError, ValueError):
            qty = 0

        return {
            "OlpnId": str(olpn_id),
            "ItemId": str(item_id),
            "InitialQuantity": qty,
            "OrderId": str(order_id),
        }

    def pack_complete_payload(self):
        if not self.olpn_search_payload:
            logging.error("No payload returned from Wave Information for pack complete payload creation")
            return None

        plant = self.olpn_search_payload['Plant']
        env = self.olpn_search_payload['Env']
        payloads = self.olpn_search_payload['Result']
        now = datetime.datetime.today()
        event_identifier = f"{plant}-{now.strftime('%Y%m%d')}-{uuid.uuid1()}"
        # event_identifier = f"{plant}-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-525-{random.randrange(10000000000, 99999999999)}"
        event_time_stamp = now.isoformat(timespec='seconds')
        grouped_by_olpn = defaultdict(list)
        for payload in payloads:
            normalized = self._normalize_item_row(payload)
            if normalized is None:
                logging.warning(f"Skipping malformed pack complete row: {payload}")
                continue
            grouped_by_olpn[normalized["OlpnId"]].append(normalized)

        pack_complete_payload = []
        for olpn_id, olpn_items in grouped_by_olpn.items():
            first_row = olpn_items[0]
            pack_complete_payload_created = {
                    "nodeAPI": {
                        "sourceSystemName": "NODE_PACK_AUDIT_AND_VAS_1081", "eventTypeCode": "PACKGOODSHOLDER",
                        "eventIdentifier": event_identifier, "eventTimestamp": event_time_stamp,
                        "eventTimeZoneCode": "UTCZ",
                        "businessKeyStructureText": "distributionCenterCd|transportgoodsholderId",
                        "businessKeyValueText": f"{plant}|{olpn_id}",
                        "packGoodsHolderRequest": {
                            "distributionCenterCd": str(plant), "nodeDistributionOrderId": str(first_row['OrderId']),
                            "transportGoodsHolderId": str(olpn_id),
                            "laborActivityId": "", "transactionId": "", "containerTypeId": "", "criteriaID": "",
                            "toteId": None,
                            "items": [
                                {
                                    "productCode": row["ItemId"],
                                    "countryOfOrigin": None,
                                    "packedQuantity": row["InitialQuantity"],
                                    "shortedQuantity": 0
                                }
                                for row in olpn_items
                            ]
                        }
                    }
                }
            pack_complete_payload.append(pack_complete_payload_created)

        if not pack_complete_payload:
            logging.error("No valid pack complete payload rows were built.")
            return None

        self.all_pack_complete_payload = {
            'Plant': plant, 'Env': env, 'Payloads': pack_complete_payload
        }
        return self.all_pack_complete_payload


if __name__ == '__main__':
    pack_olpns = Pack_Complete_Payload().pack_complete_payload()
    print(json.dumps(pack_olpns, indent=4))