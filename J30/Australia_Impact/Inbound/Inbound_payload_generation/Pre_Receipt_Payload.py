import logging
from typing import List, Dict, Any

from Australia_Impact.Inbound.Inbound_payload_generation.Inbound_Delivery_Payload import (
    Inbound_Delivery_Payload,
)

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Pre_Reciept_Payload:
    def __init__(self):
        self.inbound_delivery_payload = Inbound_Delivery_Payload()

    def pre_receipt_generate_payloads(self) -> List[Dict[str, Any]]:
        payloads = self.inbound_delivery_payload.generate_payloads()
        if not payloads:
            logging.warning("No inbound delivery payloads were generated.")
            return []
        return payloads