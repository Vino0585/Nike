import pandas as pd
import logging

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from Payload_generation.Worksheet_extract import Worksheet
from Payload_generation.Get_LPN_List_From_ASN import lpn_list_from_asn

class iLPN_Information_Payload:

    def __init__(self):
        self.worksheet = Worksheet()
        self.all_lpn_information_payload = []

    def create_lpn_information_payloads(self) -> list:
        lpn_information_data = self.worksheet.extract_relpn_list()

        if not lpn_information_data:
            logging.info("No Valid LPN Information parameter found, cannot create any payloads for LPN Information task")
            return []

        for entry in lpn_information_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            lpn_id_raw = entry.get("LPN_ID")
            asn_id_raw = entry.get("ASN_ID")

            lpn_id_string = str(lpn_id_raw) if pd.notna(lpn_id_raw) and lpn_id_raw != '' else None
            asn_id = str(asn_id_raw) if pd.notna(asn_id_raw) and asn_id_raw != '' else None

            if not all([plant, envn, (asn_id or lpn_id_string)]):
                logging.info(f"Skipping entry due to missing data: {entry}")
                continue

            lpn_list = []
            if asn_id:
                logging.info(f"Found ASN(S) '{asn_id}'. Searching for associated LPNs...")
                search_tasks = []
                for single_asn in asn_id.split(';'):
                    single_asn = single_asn.strip()
                    param = {
                        'plant': plant,
                        'environment': envn,
                        'asn_ids': [single_asn.strip()]
                        }
                    search_tasks.append(param)

                if search_tasks:
                    asn_searcher = lpn_list_from_asn()
                    lpn_list_from_asn_search = asn_searcher.create_from_asn_list_of_lpn(search_tasks)
                    for lpn in lpn_list_from_asn_search:
                        lpn_list.extend(lpn)

            elif lpn_id_string:
                logging.info(f"Using LPNs from worksheet: '{lpn_id_string}'")
                lpn_list = [lpn.strip() for lpn in lpn_id_string.split(';')]

            lpn_list_str = ','.join(f"'{lpn}'" for lpn in lpn_list)

            lpn_each_payload = {
                    "Query": f"LpnId in ({lpn_list_str})"
                }

            per_environment = {
                "environment": envn,
                "plant": plant,
                "LPN_Information": lpn_each_payload
            }

            self.all_lpn_information_payload.append(per_environment)

        return self.all_lpn_information_payload

    def parse_report_lpn_receiving_response(self, response_data: dict) -> list:
        """
        Parses the ASN API response and extracts key fields into a list of dictionaries.
        This function no longer writes to a file; it just returns the data.
        """
        if not response_data:
            logging.error("-> Success, but no ASN data was returned in the response.")
            return []

        extracted_rows = []
        for lpn in response_data:
            for detail in lpn.get("LpnDetail", []):
                row = {
                    "LPN_ID": lpn.get("LpnId"),
                    "LPN_STATUS": lpn.get("LpnStatusId"),
                    "ASN_ID": lpn.get("AsnId"),
                    "Diversion_Code": lpn.get("DiversionCodeId"),
                    "Updated_by": lpn.get("UpdatedBy"),
                    "Item": detail.get("ItemId"),
                    "Shipped_Quantity": detail.get("ShippedQuantity"),
                    "Plant": lpn.get("OrgId"),
                    "Length": lpn.get("Extended").get("LpnLength"),
                    "Width": lpn.get("Extended").get("LpnWidth"),
                    "Height": lpn.get("Extended").get("LpnHeight"),
                    "Allocation_Type": lpn.get("AllocationTypeId"),
                    "Invn_attrib": detail.get("InventoryAttribute1"),
                    "PurchaseOrderId": lpn.get("PurchaseOrderId")
                }
                extracted_rows.append(row)
        return extracted_rows

    def parse_master_lpn_response(self, response_data: dict) -> list:
        """
        Parses the ASN API response and extracts key fields into a list of dictionaries.
        This function no longer writes to a file; it just returns the data.
        """
        if not response_data:
            logging.error("-> Success, but no ASN data was returned in the response.")
            return []

        extracted_rows = []
        for lpn in response_data:
            row = {
                "LPN_ID": lpn.get("LpnId"),
                "LPN_STATUS": lpn.get("LpnStatusId"),
                "Diversion_Code": lpn.get("DiversionCodeId"),
                "Updated_by": lpn.get("UpdatedBy")
            }
            extracted_rows.append(row)
        return extracted_rows

    # def parse_report_lpn_inventory_response(self, response_data: dict) -> list:
    #     """
    #     Parses the ASN API response and extracts key fields into a list of dictionaries.
    #     This function no longer writes to a file; it just returns the data.
    #     """
    #     if not response_data:
    #         logging.error("-> Success, but no ASN data was returned in the response.")
    #         return []
    #
    #     extracted_rows = []
    #     for lpn in response_data:
    #         for detail in lpn.get("LpnDetail", []):
    #             row = {
    #                 "LPN_ID": lpn.get("LpnId"),
    #                 "LPN_STATUS": lpn.get("LpnStatusId"),
    #                 "ASN_ID": lpn.get("AsnId"),
    #                 "Diversion_Code": lpn.get("DiversionCodeId"),
    #                 "Updated_by": lpn.get("UpdatedBy"),
    #                 "Item": detail.get("ItemId"),
    #                 "Shipped_Quantity": detail.get("ShippedQuantity"),
    #                 "Plant": lpn.get("OrgId"),
    #                 "Length": lpn.get("Extended").get("LpnLength"),
    #                 "Width": lpn.get("Extended").get("LpnWidth"),
    #                 "Height": lpn.get("Extended").get("LpnHeight"),
    #                 "Allocation_Type": lpn.get("AllocationTypeId"),
    #                 "Invn_attrib": detail.get("InventoryAttribute1"),
    #                 "PurchaseOrderId": lpn.get("PurchaseOrderId")
    #             }
    #             extracted_rows.append(row)
    #     return extracted_rows


#
# initiation = iLPN_Information_Payload()
# payload = initiation.create_lpn_information_payloads()
# for load in payload:
#     print(load)