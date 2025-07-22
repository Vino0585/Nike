import uuid
import datetime as dt

from Archive.ImportASNDev import asn_id
from Payload_generation.Worksheet_extract import Worksheet
from ASN_Search import create_from_asn_list_of_lpn


class Goods_Holder:

    def __init__(self):
        self.worksheet = Worksheet()
        # This instance variable isn't strictly necessary if only used in one method,
        # but we'll keep it for consistency with your original structure.
        self.all_goods_holder_announced = []

    def create_goods_holder_announced_payloads(self) -> list:
        """
        Generates a list of GOODSHOLDER_ANNOUNCED payloads from worksheet data.
        """
        goods_holder_data = self.worksheet.goods_holder_announced()

        if not goods_holder_data:
            print("No valid item parameters found, cannot create any payloads.")
            return []

        payloads = []

        for entry in goods_holder_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            lpn_id_string = entry.get("LPN_ID")

            # --- CHANGE 1: Simplified the data check ---
            # We no longer need to check for a timestamp from the sheet.
            if not all([plant, envn, lpn_id_string]):
                print(f"Skipping entry due to missing data: {entry}")
                continue

            asn_id = entry.get("ASN")
            if asn_id:
                asn_ids = asn_id.split(';')
                for asn in asn_ids
                    param = {
                        'plant': plant,
                        'environment': envn,
                        'asn_ids': asn_id
                    }
                get_lpn =

            # --- CHANGE 2: Generate the current timestamp in UTC ---
            # This creates a timezone-aware datetime object for the current moment.
            # The try/except block is no longer needed.
            aware_timestamp = dt.datetime.now(dt.timezone.utc)
            iso_timestamp_str = aware_timestamp.isoformat()

            lpn_list = lpn_id_string.split(';')

            for lpn in lpn_list:
                event_id = str(uuid.uuid4())

                payload = {
                    "event": {
                        "type": "GOODSHOLDER_ANNOUNCED",
                        "tmst": iso_timestamp_str,
                        "timezone": "UTC+00:00",
                        "id": event_id,
                        "correlationId": None,
                        "distributionCenterCd": f"NODE_{plant}",
                        "technicalSolutionSourceCd": "NAS_V001",
                        "version": "1.0.0"
                    },
                    "data": {
                        "distributionCenterCd": f"NODE_{plant}",
                        "goodsholderId": lpn.strip(), # .strip() removes accidental whitespace
                        "announcedByDeviceId": "TYT-12345678",
                        "executionTmst": iso_timestamp_str
                    }
                }
                payloads.append(payload)

            gha_payload = {
                'environment': envn,
                'plant': plant,
                'GHAPayload': payloads
            }

            self.all_goods_holder_announced.append(gha_payload)

        return self.all_goods_holder_announced


# # It's best practice to run scripts within this block.
# # Also, avoid using 'list' as a variable name as it shadows the built-in type.
# if __name__ == "__main__":
#     gh_announced = Goods_Holder()
#     generated_payloads = gh_announced.create_goods_holder_announced_payloads()
#     # Pretty-print the result for better readability
#     import json
#     print(json.dumps(generated_payloads, indent=2))