from Inbound.Payload_generation.Worksheet_extract import Worksheet


class ASN_Verify_Payload:
    def __init__(self):
        self.worksheet = Worksheet()
        self.all_verify_asn_worksheet_parameter = self.worksheet.verify_asn_worksheet_extract()
        self.all_worksheet_verify_asn_payload = []
        self.all_verify_asn_payload = []
        self.get_parse_asn_verify_param = []

    def parse_asn_verify_worksheet(self) -> list:
        if not self.all_verify_asn_worksheet_parameter:
            print("No valid ASN parameters found in the worksheet.")
            return None

        for entry in self.all_verify_asn_worksheet_parameter:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id_str = entry.get("ASN_ID")

            if not (asn_id_str and isinstance(asn_id_str, str)):
                print(f"--> WARNING: Skipping row for Plant {plant} due to invalid or empty ASNID.")
                continue

            # Cleanly split, strip whitespace, and filter out any empty strings
            cleaned_asn_ids = [item.strip() for item in asn_id_str.split(';') if item.strip()]

            if not cleaned_asn_ids:
                print(f"--> WARNING: Skipping row for Plant {plant} as no valid ASN IDs were found after cleaning.")
                continue


            self.all_worksheet_verify_asn_payload.append({
                                                "plant": str(plant),
                                                "environment": envn,
                                                "asn_ids": cleaned_asn_ids
                                                })
        return self.all_worksheet_verify_asn_payload

    def create_verify_asn_payload(self):

        self.parse_asn_verify_worksheet()

        if not self.all_worksheet_verify_asn_payload:
            print("No valid ASN parameters found in the worksheet.")

        for entry in self.all_worksheet_verify_asn_payload:
            plant = entry.get("plant")
            envn = entry.get("environment")
            asn_ids = entry.get("asn_ids")

            query = []
            for asn in asn_ids:
                body = {
                    "AsnId": asn
                }
                query.append(body)

            all_query = {
                "Plant": plant,
                "Environment": envn,
                "Query": query
            }

            self.all_verify_asn_payload.append(all_query)

        return self.all_verify_asn_payload

# initiate = ASN_Verify_Payload()
# result = initiate.create_verify_asn_payload()
# print(result)