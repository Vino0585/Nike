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
        self.all_search_iLPN_parameters = self.inventory_worksheet.search_iLPN_parameters()

    def create_lpn_receiving_payload(self) -> list:

        if not self.all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        template_lpn_receiving_structure = {
            "AsnId": None, "LpnId": None, "LpnStatus": None, "DiversionCodeId": None, "PreReceiptStatusId": None,
            "LpnDetail": {"ItemId": None, "InventoryAttribute1": None, "UpdatedBy": None, "PurchaseOrderId": None,
                          "ShippedQuantity": None}
            }

        for entry in self.all_search_iLPN_parameters:
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

        if not self.all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        template_lpn_inventory_structure = {
        "ShipmentId": None, "AsnId": None, "IlpnId": None, "ItemId": None, "CurrentLocationId": None,
        "PreviousLocationId": None, "DestinationLocationId": None,  "Status": None, "Height": None,
        "Width": None, "Length": None, "SingleLineLpn": None, "ActualWeight": None, "Volume": None,
        "PurchaseOrderId": None
        }

        for entry in self.all_search_iLPN_parameters:
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

    def create_ilpn_condition_code_payload(self) -> list:

        if not self.all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        for entry in self.all_search_iLPN_parameters:
            asn_id = entry['ASN_ID']
            lpn_id = entry['iLPN_ID']

            def create_inventory_package(query_string):
                payload = {
                    "Query": query_string,
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

                    query = f"Ilpn.AsnId = '{asn_id}'"
                    if query:
                        all_payloads.append(create_inventory_package(query))

            elif pd.notna(lpn_id) and str(lpn_id).strip():
                lpn_id_list = str(lpn_id).split(';')
                for lpn in lpn_id_list:
                    lpn_id = lpn.strip()
                    if not lpn_id:
                        continue

                    query = f"'Query': Ilpn.IlpnId = '{lpn_id}'"
                    if query:
                        all_payloads.append(create_inventory_package(query))

        return all_payloads

    def create_item_inventory_by_location_payload(self):

        if not self.all_search_iLPN_parameters:
            logging.error("No valid iLPN parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        full_payload = {}
        for entry in self.all_search_iLPN_parameters:
            item_id = entry['ITEM_IDS']
            status = entry['STATUS']

            LPN_STATUS_MAP = {
                'Allocated': 5000,
                'Not Allocated': 3000,
            }

            LPN_STATUS = LPN_STATUS_MAP.get(status)
            if pd.notna(item_id) and str(item_id).strip():
                item_id_list = str(item_id).split(';')
                for item_id in item_id_list:
                    item_id = item_id.strip()
                    if not item_id:
                        logging.error("Item ID not found, cannot create any payloads.")

                    payload = {
                        "ViewName": "InventoryGrid",
                        "Filters": [
                            {
                                "ViewName": "InventoryDetails", "AttributeId": "ItemId", "DataType": None,
                                "requiredFilter": "False", "Operator": "=", "FilterValues": [f"{item_id}"]
                            },
                            {
                                "ViewName": "InventoryGrid", "AttributeId": "Status", "DataType": None,
                                "requiredFilter": "False", "Operator": "=", "FilterValues": [LPN_STATUS]
                            },
                            {
                                "ViewName": "InventoryGrid", "AttributeId": "Zone", "DataType": None,
                                "requiredFilter": "False", "Operator": "=", "FilterValues": ["24"]
                            }
                        ],
                        "Page": 0, "TotalCount": -1, "SortOrder": "asc", "TimeZone": "Japan",
                        "EnableMaxCountLimit": "true", "MaxCountLimit": 25, "Size": 10
                    }
                    if payload:
                        all_payloads.append(payload)

                full_payload = {
                    "envn": entry.get("Environment"),
                    "plant": entry.get("Plant"),
                    "payload": all_payloads
                }

            return full_payload


if __name__ == '__main__':
    py = iLPN_Search_Payload()
    import pprint
    # pprint.pprint(py.create_lpn_receiving_payload())
    # pprint.pprint(py.create_lpn_inventory_payload())
    # pprint.pprint(py.create_ilpn_condition_code_payload())
    pprint.pprint(py.create_item_inventory_by_location_payload())