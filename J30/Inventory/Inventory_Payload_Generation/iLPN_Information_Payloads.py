# Program to create payload to generate query for different iLPN searches.
from Inventory.Inventory_Payload_Generation.Inventory_WorkSheet_Extract import Inventory_WorkSheet_Extract
import logging
import pandas as pd

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class iLPN_Search_Payload:
    def __init__(self):
        self.inventory_worksheet = Inventory_WorkSheet_Extract()
        self.all_iLPN_search_payload = []

    def create_lpn_receiving_payload(self) -> list:
        all_search_iLPN_parameters = self.inventory_worksheet.search_iLPN_parameters()

        if not all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        template_lpn_receiving_structure = {
            "AsnId": None, "LpnId": None, "LpnStatus": None, "DiversionCodeId": None, "PreReceiptStatusId": None,
            "LpnDetail": {"ItemId": None, "InventoryAttribute1": None, "UpdatedBy": None, "PurchaseOrderId": None,
                          "ShippedQuantity": None}
            }

        for entry in all_search_iLPN_parameters:
            asn_id = entry['ASN_ID']
            lpn_id = entry['iLPN_ID']

            def create_receiving_package(query_string):
                payload = {
                    "Query": query_string,
                    "Template": template_lpn_receiving_structure,
                }
                return {
                    "envn": entry.get("Environment"),
                    "plant": entry.get("Plant"),
                    "payload": payload
                }

            query = None
            if pd.notna(asn_id) and str(asn_id).strip():
                asn_id_list = str(asn_id).split(';')
                for asn in asn_id_list:
                    asn_id = asn.strip()
                    if not asn_id:
                        continue

                    query = f"AsnId = '{asn_id}'"
                    if query:
                        all_payloads.append(create_receiving_package(query))

            elif pd.notna(lpn_id) and str(lpn_id).strip():
                lpn_id_list = str(lpn_id).split(';')
                for lpn in lpn_id_list:
                    lpn_id = lpn.strip()
                    if not lpn_id:
                        continue

                    query = f"'Query': LpnId = '{lpn_id}'"
                    if query:
                        all_payloads.append(create_receiving_package(query))

        return all_payloads


    def create_lpn_inventory_payload(self) -> list:
        all_search_iLPN_parameters = self.inventory_worksheet.search_iLPN_parameters()

        if not all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        template_lpn_inventory_structure = {
        "ShipmentId": None, "AsnId": None, "IlpnId": None, "ItemId": None, "CurrentLocationId": None,
        "PreviousLocationId": None, "DestinationLocationId": None,  "Status": None, "Height": None,
        "Width": None, "Length": None, "SingleLineLpn": None, "ActualWeight": None, "Volume": None,
        "PurchaseOrderId": None
        }

        for entry in all_search_iLPN_parameters:
            asn_id = entry['ASN_ID']
            lpn_id = entry['iLPN_ID']

            def create_inventory_package(query_string):
                payload = {
                    "Query": query_string,
                    "Template": template_lpn_inventory_structure,
                }
                return {
                    "envn": entry.get("Environment"),
                    "plant": entry.get("Plant"),
                    "payload": payload
                }

            query = None
            if pd.notna(asn_id) and str(asn_id).strip():
                asn_id_list = str(asn_id).split(';')
                for asn in asn_id_list:
                    asn_id = asn.strip()
                    if not asn_id:
                        continue

                    query = f"AsnId = '{asn_id}'"
                    if query:
                        all_payloads.append(create_inventory_package(query))

            elif pd.notna(lpn_id) and str(lpn_id).strip():
                lpn_id_list = str(lpn_id).split(';')
                for lpn in lpn_id_list:
                    lpn_id = lpn.strip()
                    if not lpn_id:
                        continue

                    query = f"'Query': LpnId = '{lpn_id}'"
                    if query:
                        all_payloads.append(create_inventory_package(query))

        return all_payloads


if __name__ == '__main__':
    py = iLPN_Search_Payload()
    import pprint
    pprint.pprint(py.create_lpn_receiving_payload())
    pprint.pprint(py.create_lpn_inventory_payload())