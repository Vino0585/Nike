from pathlib import Path
import requests
import pandas as pd
from collections import defaultdict
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Payload_generation.ASNPayload import Asn_Payload_Generator


def create_asns():
    """
    Generates ASN payloads, groups them by environment, and sends them to the MAWM API.
    """
    asn_gen = Asn_Payload_Generator()
    payload_packages = asn_gen.generate_payloads
    if not payload_packages:
        print("\nNo payloads were generated. Please check your Excel input and generator logic.")
        return

    payloads_by_env = defaultdict(list)
    for package in payload_packages:
        env = package.get('environment')
        payload = package.get('payload')
        if env and payload:
            payloads_by_env[env].append(payload)
        else:
            print(f"--> WARNING: Skipping malformed package: {package}")

    # This list will collect data for the final report from ALL successful payloads
    extracted_report_data = []

    for environment, payloads in payloads_by_env.items():
        print(f"\n{'='*20} Processing {len(payloads)} Payloads for Environment: {environment.upper()} {'='*20}")
        if not payloads:
            print(f"--> WARNING: Skipping empty payload list for environment {environment.upper()}.")
            continue

        try:
            plant_id_for_token = payloads[0].get('OrgId')
            if not plant_id_for_token:
                print(f"--> FATAL ERROR: Cannot get token. First payload for {environment.upper()} is missing 'OrgId'.")
                continue

            token_handler = Get_Token(env=environment.lower(), plant=plant_id_for_token)
            bearer_token = token_handler.get_bearer()
            print(f"Successfully retrieved token for {environment.upper()} environment.")

            env_handler = AWM_Env()

            for i, payload_to_send in enumerate(payloads):
                try:
                    plant_id = payload_to_send['OrgId']
                    print(f"\n--- [{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id} ---")

                    env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
                    url_value = env_handler.get_program_url(program=Path(__file__).stem)
                    print(f"Sending payload to URL: {url_value}")

                    headers = {
                        "content-type": "application/json",
                        "organization": str(plant_id),
                        "location": str(plant_id),
                        "authorization": 'Bearer ' + bearer_token
                    }

                    response = requests.post(url=url_value, headers=headers, json=payload_to_send)
                    response.raise_for_status()

                    response_data = response.json()
                    print(f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")

                    # ==================================================================
                    # CORRECTED REPORT LOGIC - MOVED INSIDE THE SUCCESS BLOCK
                    # This now runs for each successfully processed payload.
                    # ==================================================================
                    try:
                        # Use .get() for safe access from the payload that was just sent
                        asn_id = payload_to_send.get('AsnId')
                        origin_facility = payload_to_send.get('OriginFacilityId')
                        lpn_list = payload_to_send.get('Lpn', []) # Default to empty list
                        carrier_id = payload_to_send.get('CarrierId')

                        for lpn in lpn_list:
                            lpn_id = lpn.get('LpnId')
                            # Ensure LpnDetail exists and is not empty before accessing it
                            if lpn.get('LpnDetail'):
                                item_id = lpn['LpnDetail'][0].get('ItemId')
                                quantity = lpn['LpnDetail'][0].get('ShippedQuantity')

                                report_entry = {
                                    "ENVN": environment,
                                    "ASN_ID": asn_id,
                                    "LPN_ID": lpn_id,
                                    "ITEM_ID": item_id,
                                    "QTY": quantity,
                                    "O_FACILITY": origin_facility,
                                    "Carrier": carrier_id
                                }
                                extracted_report_data.append(report_entry)

                    except (TypeError, ValueError, KeyError) as e:
                        print(f"--> WARNING: Could not parse report data from successful payload. Malformed data? Error: {e}")

                except KeyError as e:
                    print(f"--> ERROR: Could not process payload {i + 1}. Data is malformed. Missing key: {e}")
                except requests.exceptions.RequestException as e:
                    print(f"--> ERROR: API request failed for payload {i + 1}: {e}")
                    if e.response is not None:
                        print(f"--> Status Code: {e.response.status_code}, Response: {e.response.text}")
                except Exception as e:
                    print(f"--> ERROR: An unexpected error occurred for payload {i + 1}: {e}")

        except Exception as e:
            print(f"--> FATAL ERROR: Could not process batch for environment {environment.upper()}. Error: {e}")

    # 12. Generate the final report from ALL collected data
    if extracted_report_data:
        print("\n" + "=" * 25 + " Generating Report " + "=" * 25)
        try:
            report_df = pd.DataFrame(extracted_report_data)

            # Define the Output path.
            output_dir = Path("Output_files")
            output_dir.mkdir(parents=True, exist_ok=True) # Just safe guaring.
            output_filepath = output_dir / "ASN_Creation_Report.xlsx"

            report_df.to_excel(output_filepath, index=False)
            print(f"Successfully created report: {output_filepath}")
        except Exception as e:
            print(f"--> ERROR: Failed to create Excel report. Error: {e}")
    else:
        print("\nNo data was successfully processed to generate a report.")


if __name__ == "__main__":
    create_asns()


# # Version 1
# import requests
# import pandas as pd
# from pathlib import Path
# from collections import defaultdict  # <-- Added for easier grouping
# from Get_Token import Get_Token
# from Payload_generation.WM_Environment import AWM_Env
# from J30.Payload_generation.ASNPayload import Asn_Payload_Generator
#
# def create_asns():
#     """
#     Generates ASN payloads, groups them by environment, and sends them to the MAWM API.
#     """
#     # 1. Create an instance of the generator
#     asn_gen = Asn_Payload_Generator()
#
#     # 2. Generate a list of payload "packages"
#     payload_packages = asn_gen.generate_payloads
#     if not payload_packages:
#         print("\nNo payloads were generated. Please check your Excel input and generator logic.")
#         return
#
#     # 3. Group payloads by their target environment for efficient processing.
#     payloads_by_env = defaultdict(list)
#     extracted_report = []
#     for package in payload_packages:
#         env = package.get('environment')
#         payload = package.get('payload')
#         if env and payload:
#             payloads_by_env[env].append(payload)
#         else:
#             print(f"--> WARNING: Skipping malformed package: {package}")
#             continue  # Skip to the next package if this one is bad
#
#     # 4. Loop through each environment group and process its payloads
#     for environment, payloads in payloads_by_env.items():
#         print(f"\n{'='*20} Processing {len(payloads)} Payloads for Environment: {environment.upper()} {'='*20}")
#         try:
#             # 5. Get token ONCE for the entire environment batch
#             token_handler = Get_Token(environment.lower())
#             bearer_token = token_handler.get_bearer()
#             print(f"Successfully retrieved token for {environment.upper()} environment.")
#
#             # Create a single environment handler for this batch
#             env_handler = AWM_Env()
#
#             # 6. Now loop through the individual payloads for this environment
#             for i, payload_to_send in enumerate(payloads):
#                 try:
#                     # 7. Unpack data for the individual payload
#                     plant_id = payload_to_send['OrgId']
#
#                     print(f"\n--- [{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id} ---")
#
#                     # 8. Get URL for THIS payload's specific plant
#                     env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
#                     url_value = env_handler.get_program_url(program=Path(__file__).stem)
#                     print(f"Sending payload to URL: {url_value}")
#
#                     # 9. Build headers, reusing the token for this environment
#                     headers = {
#                         "content-type": "application/json",
#                         "organization": str(plant_id),
#                         "location": str(plant_id),
#                         "authorization": 'Bearer ' + bearer_token
#                     }
#
#                     # 10. Send the request for this single payload
#                     response = requests.post(url=url_value, headers=headers, json=payload_to_send)
#                     response.raise_for_status()
#
#                     response_data = response.json()
#                     print(
#                         f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")
#                     print(response_data)
#                 except KeyError as e:
#                     print(f"--> ERROR: Could not process payload {i + 1} in {environment.upper()}. Data is malformed. Missing key: {e}")
#                 except requests.exceptions.RequestException as e:
#                     print(f"--> ERROR: API request failed for payload {i + 1} in {environment.upper()}: {e}")
#                     if e.response is not None:
#                         print(f"--> Status Code: {e.response.status_code}")
#                         print(f"--> Server Response: {e.response.text}")
#                 except Exception as e:
#                     print(f"--> ERROR: An unexpected error occurred for payload {i + 1} in {environment.upper()}: {e}")
#
#         except Exception as e:
#             # This catches errors at the environment level (e.g., getting a token)
#             print(f"--> FATAL ERROR: Could not process batch for environment {environment.upper()}. Error: {e}")
#
#     # 11. Uploading the extracted report to an Excel sheet.
#         # Safely extract data for the report
#     try:
#         LPN_Info = payload['Lpn']
#         ASN = LPN_Info[0]['AsnId']
#         O_FACILITY = payload['OriginFacilityId']
#         for num_lpn in range(len(LPN_Info)):
#             LPN_ID = LPN_Info[num_lpn]['LpnId']
#             ITEM_ID = LPN_Info[num_lpn]['LpnDetail'][0]['ItemId']
#             QTY = LPN_Info[num_lpn]['LpnDetail'][0]['ShippedQuantity']
#
#             report_entry = {
#                 "ENVN": env,
#                 "ASN_ID": ASN,
#                 "LPN_ID": LPN_ID,
#                 "ITEM_ID": ITEM_ID,
#                 "QTY": QTY,
#                 "O_FACILITY": O_FACILITY
#             }
#             extracted_report.append(report_entry)
#
#     except (KeyError, IndexError) as e:
#         print(f"--> WARNING: Could not extract report data from payload. Malformed data? Error: {e}")
#
#     if extracted_report:
#         print("\n" + "=" * 25 + " Generating Report " + "=" * 25)
#         try:
#             report_df = pd.DataFrame(extracted_report)
#             output_filename = '/Users/vgana3/Documents/Pycharm/MAWM/J30/Payload_generation/ASN_Creation_Report.xlsx'
#             report_df.to_excel(output_filename, index=False)
#             print(f"Successfully created report: {output_filename}")
#         except Exception as e:
#             print(f"--> ERROR: Failed to create Excel report. Error: {e}")
#     else:
#         print("\nNo data was available to generate a report.")
#
#
# if __name__ == "__main__":
#     create_asns()

# Useful Query for later use:
# # --- START: DEBUGGING PRINTS ---
# print("=" * 50)
# print(f"DEBUG: Request URL: {url_value}")
# print(f"DEBUG: Request Method: POST")
# print("DEBUG: Request Headers:")
# print(json.dumps(headers, indent=2))
# print("DEBUG: Request Body:")
# print(json.dumps(payload_to_send, indent=2))
# print("=" * 50)
# print(bearer_token)
