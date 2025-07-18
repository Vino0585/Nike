import pandas as pd
from Payload_generation.Worksheet_extract import Worksheet


class ASN_Search_Payload:
    def __init__(self):
        self.worksheet = Worksheet()
        self.all_asn_search_worksheet_parameter = self.worksheet.search_asn_extract_parameters()
        self.all_asn_search_payload = []


    def parse_asn_search_worksheet(self) -> list:
        if not self.all_asn_search_worksheet_parameter:
            print("No valid ASN parameters found in the worksheet.")
            return None

        for entry in self.all_asn_search_worksheet_parameter:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id_str = entry.get("ASNID")

            if not (asn_id_str and isinstance(asn_id_str, str)):
                print(f"--> WARNING: Skipping row for Plant {plant} due to invalid or empty ASNID.")
                continue

            # Cleanly split, strip whitespace, and filter out any empty strings
            cleaned_asn_ids = [item.strip() for item in asn_id_str.split(';') if item.strip()]

            if not cleaned_asn_ids:
                print(f"--> WARNING: Skipping row for Plant {plant} as no valid ASN IDs were found after cleaning.")
                continue


            self.all_asn_search_payload.append({
                                                "plant": str(plant),
                                                "environment": envn,
                                                "asn_ids": cleaned_asn_ids  # Store as a list for easier processing later
                                                })
        return self.all_asn_search_payload



# initiate = ASN_Search_Payload()
# result = initiate.create_asn_search_payloads()
# print(result)