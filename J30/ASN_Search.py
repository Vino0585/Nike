import requests
import json
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from pathlib import Path
import pandas as pd
from Payload_generation.ASN_Search_Payload import ASN_Search_Payload

# --- Configuration ---
# Centralize configuration variables for easy changes.
output_dir = Path("Output_files")
output_dir.mkdir(parents=True, exist_ok=True)
OUTPUT_FILENAME = output_dir / "ASN_Search_Results.xlsx"

def parse_asn_response(response_data: dict) -> list:
    """
    Parses the ASN API response and extracts key fields into a list of dictionaries.
    This function no longer writes to a file; it just returns the data.
    """
    if not response_data.get("data"):
        print("-> Success, but no ASN data was returned in the response.")
        return []

    extracted_rows = []
    for asn in response_data.get("data", []):
        for lpn in asn.get("Lpn", []):
            for detail in lpn.get("LpnDetail", []):
                row = {
                    "AsnId": asn.get("AsnId"),
                    "AsnStatus": asn.get("AsnStatus"),
                    "AsnOriginTypeId": asn.get("AsnOriginTypeId"),
                    "LpnId": lpn.get("LpnId"),
                    "LpnStatus": lpn.get("LpnStatus"),
                    "ItemId": detail.get("ItemId"),
                    "ShippedQty": detail.get("ShippedQuantity"),
                    "UpdatedBy": detail.get("UpdatedBy"),
                    "UpdatedTimestamp": detail.get("UpdatedTimestamp"),
                    "OrgId": detail.get("OrgId"),
                    "BOL": asn.get('BillOfLadingNumber'),
                    "ProNbr": asn.get('ProNumber'),
                    "Carrier": asn.get('CarrierId'),
                    "LPNSizeType": lpn.get('LpnSizeTypeId'),
                    "Length": lpn['Extended'].get('LpnLength'),
                    "Height": lpn['Extended'].get('LpnHeight'),
                    "Width": lpn['Extended'].get('LpnWidth'),
                    "Origin_facility": asn.get('OriginFacilityId'),
                    "TrailerNbr": asn.get('TrailerId')
                }
                extracted_rows.append(row)
    return extracted_rows


def search_asn_sending():
    """Main function to orchestrate the ASN search process."""
    asn_search_payload_init = ASN_Search_Payload()
    search_tasks = asn_search_payload_init.parse_asn_search_worksheet()
    if not search_tasks:
        print("\nScript finished: No valid search tasks to process.")
        return

    all_results = []  # --- Collect all results here before writing to file ---
    raw_data = None
    response_data = ''
    # --- Loop correctly over each task ---
    # The try/except block is now INSIDE the loop to handle errors per task.
    for i, task in enumerate(search_tasks):
        # --- FIX: Use correct, lowercase dictionary keys ---
        envn = task['environment']
        plant_id = task['plant']
        asn_ids = task['asn_ids']

        print(f"\n{'='*20} Processing Task {i+1}/{len(search_tasks)}: Plant {plant_id} ({envn.upper()}) {'='*20}")

        try:
            # --- 1. Authentication ---
            token_handler = Get_Token(env=envn.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()
            print("Successfully retrieved token.")

            # --- 2. URL Setup ---
            awm_env = AWM_Env()
            awm_env.get_wm_host(host=envn.lower(), facility=plant_id)
            program_name = Path(__file__).stem
            api_url = awm_env.get_program_url(program=program_name)
            print(f"Target URL: {api_url}")

            # --- 3. Request Headers & Payload ---
            headers = {
                "Content-Type": "application/json",
                "organization": plant_id, # Common practice is to use 'organization' and 'location'
                "location": plant_id,
                "Authorization": f"Bearer {bearer_token}"
            }

            # Creates a string like "('ASN1','ASN2','ASN3')"
            query_values = "','".join(asn_ids)
            # --- Correctly format the 'in' query string ---
            query_string = f"AsnId in ('{query_values}')"

            payload = {"Query": query_string}
            print(f"Sending Payload: {json.dumps(payload)}")

            # --- 4. API Call ---
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            raw_data = response_data.get("data")

            # --- 5. Process and Collect Response ---
            # The parse function now returns data instead of writing to a file
            extracted_data = parse_asn_response(response_data)
            if extracted_data:
                print(f"-> Success: Found {len(extracted_data)} detail rows for this task.")
                all_results.extend(extracted_data) # Add results to the master list

        except requests.exceptions.HTTPError as http_err:
            print(f"❌ HTTP error occurred: {http_err}")
            if http_err.response:
                print(f"Response content: {http_err.response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"❌ A request error occurred: {req_err}")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

    # --- 6. Final Export ---
    # This block runs once after all tasks are completed.
    if not all_results:
        print("\n--- Script finished, but no results were collected from any API calls. ---")
        return

    print(f"\n{'=' * 25} Consolidating and Exporting Results {'=' * 25}")
    try:
        # Create the main DataFrame with the parsed results
        df_details = pd.DataFrame(all_results)
        print("--- ASN Details ---")
        print(df_details.to_string(index=False))

        # Use pd.ExcelWriter to save multiple sheets to the SAME file
        with pd.ExcelWriter(OUTPUT_FILENAME, engine='openpyxl') as writer:
            # Write the first sheet
            df_details.to_excel(writer, sheet_name="ASN_Details", index=False)

            # --- Correctly handle and write the raw data ---
            # Check if raw_data (from the last successful call) exists
            if raw_data:

                for each_payload in raw_data:
                    # Convert the entire raw dictionary to a formatted JSON string
                    raw_json_string = json.dumps(each_payload, indent=4)
                    # Create a simple DataFrame to hold this string
                    df_raw = pd.DataFrame({'Raw_Payload': [raw_json_string]})

                    # Write the second sheet
                    df_raw.to_excel(writer, sheet_name="Raw_ASN_Payload", index=False)
                    print("\n--- Raw Payload updated in Excel Sheet: Raw_ASN_Payload ---")

        print(f"\n✅ Successfully exported {len(df_details)} total rows to '{OUTPUT_FILENAME}'")

    except Exception as e:
        print(f"\n❌ Error exporting final report to Excel: {e}")

    return response_data


def create_from_asn_list_of_lpn() -> list:
    get_data = search_asn_sending()
    if not get_data:
        print("-> Success, but no ASN data was returned in the response.")
        return []

    extracted_lpn_ids = []
    for asn in get_data.get("data", []):
        for lpn in asn.get("Lpn", []):
            row = {
                "LpnId": lpn.get("LpnId")
            }
            extracted_lpn_ids.append(row)
    return extracted_lpn_ids


if __name__ == "__main__":
    search_asn_sending()