import logging

from Inventory.Inventory_Payload_Generation.Inventory_WorkSheet_Extract import Inventory_WorkSheet_Extract
import pandas as pd

class ItemCubiScanPayload():
    def __init__(self):
        self.worksheet = Inventory_WorkSheet_Extract()

    def create_item_cubi_scan_payload(self):
        try:
            list_of_datadict = self.worksheet.cubiscan_worksheet_information()
            if list_of_datadict is None:
                logging.error("Error: Worksheet method returned None. Halting generation.")
                return []
            except Exception as e:
            logging.error(f"An unexpected error occurred while extracting data from the worksheet: {e}")
            return []
