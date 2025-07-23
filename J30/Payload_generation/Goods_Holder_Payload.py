import uuid
import datetime as dt
import pandas as pd

from Payload_generation.Worksheet_extract import Worksheet
from Payload_generation.Get_LPN_List_From_ASN import lpn_list_from_asn


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
            lpn_id_raw = entry.get("LPN_ID")
            asn_id_raw = entry.get("ASN_ID")

            lpn_id_string = str(lpn_id_raw) if pd.notna(lpn_id_raw) and lpn_id_raw != '' else None
            asn_id = str(asn_id_raw) if pd.notna(asn_id_raw) and asn_id_raw != '' else None

            # --- CHANGE 1: Simplified the data check ---
            # We no longer need to check for a timestamp from the sheet.
            if not all([plant, envn, (asn_id or lpn_id_string)]):
                print(f"Skipping entry due to missing data: {entry}")
                continue

            lpn_list = []
            if asn_id:
                print(f"Found ASN(s) '{asn_id}'. Searching for associated LPNs...")
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
                print(f"Using LPNs from worksheet: '{lpn_id_string}'")
                lpn_list = [lpn.strip() for lpn in lpn_id_string.split(';')]

            # --- CHANGE 2: Generate the current timestamp in UTC ---
            entry_payloads = []
            for lpn in lpn_list:
                event_id = str(uuid.uuid4())
                aware_timestamp = dt.datetime.now(dt.timezone.utc)
                iso_timestamp_str = aware_timestamp.isoformat()
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
                        "goodsholderId": lpn, # .strip() removes accidental whitespace
                        "announcedByDeviceId": "TYT-12345678",
                        "executionTmst": iso_timestamp_str
                    }
                }
                entry_payloads.append(payload)

            if entry_payloads:
                gha_payload = {
                    'environment': envn,
                    'plant': plant,
                    'GHAPayload': entry_payloads
                }

                self.all_goods_holder_announced.append(gha_payload)

        return self.all_goods_holder_announced


# It's best practice to run scripts within this block.
# Also, avoid using 'list' as a variable name as it shadows the built-in type.
if __name__ == "__main__":
    gh_announced = Goods_Holder()
    generated_payloads = gh_announced.create_goods_holder_announced_payloads()
    # Pretty-print the result for better readability
    import json
    print(json.dumps(generated_payloads, indent=2))