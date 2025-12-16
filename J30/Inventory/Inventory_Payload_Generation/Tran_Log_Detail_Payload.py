import json
import logging
from xml.etree.ElementTree import indent

from Inventory.Tran_Log_Detail_Header import Tran_Log_Detail_Header_Info


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Tran_Log_Detail_Payload:
    def __init__(self):
        self.tran_log_detail_header = Tran_Log_Detail_Header_Info()
        self.tran_log_detail_header_info = self.tran_log_detail_header.create_tran_log_detail_header_inventory()
        self.all_tran_log_detail_payload = []

    def create_tran_log_detail_payload(self):
        if not self.tran_log_detail_header_info:
            logging.error('The tranlog_detail_header record returned nothing. Please check Tran_log_detail_header.py')
            return None

        logging.info(f"The total message to provide payload is {len(self.tran_log_detail_header_info)} entries")

        for entry in self.tran_log_detail_header_info:
            plant = entry.get("Plant")
            environment = entry.get("Environment")
            msg_id = entry.get("msg_id")

            if not plant and environment and msg_id:
                logging.error("Malformed data either plant or environment or msg_id is missing")
                return None

            payload = {
                "Plant": plant,
                "Environment": environment,
                "msg_id": msg_id
            }
            self.all_tran_log_detail_payload.append(payload)

        return self.all_tran_log_detail_payload

if __name__ == "__main__":
    py = Tran_Log_Detail_Payload()
    full_payload = py.create_tran_log_detail_payload()
    for payload in full_payload:
        print(payload)


