from pathlib import Path
import requests
import pandas as pd
from collections import defaultdict

from openpyxl.styles.builtins import output

from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Payload_generation.ASN_Creation_Payload import Asn_Payload_Generator


class ASN_Creation:

    def create_asns(self):
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
        output_data = []
        collected_lpn = []
        collected_asn = []
        output_file = {}

        for environment, payloads in payloads_by_env.items():
            print(f"\n{'=' * 20} Processing {len(payloads)} Payloads for Environment: {environment.upper()} {'=' * 20}")
            if not payloads:
                print(f"--> WARNING: Skipping empty payload list for environment {environment.upper()}.")
                continue

            try:
                plant_id_for_token = payloads[0].get('OrgId')
                if not plant_id_for_token:
                    print(
                        f"--> FATAL ERROR: Cannot get token. First payload for {environment.upper()} is missing 'OrgId'.")
                    continue

                token_handler = Get_Token(env=environment.lower(), plant=plant_id_for_token)
                bearer_token = token_handler.get_bearer()
                print(f"Successfully retrieved token for {environment.upper()} environment.")

                env_handler = AWM_Env()

                for i, payload_to_send in enumerate(payloads):
                    try:
                        plant_id = payload_to_send['OrgId']
                        print(
                            f"\n--- [{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} for Plant {plant_id} ---")

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
                        print(
                            f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")

                        # ==================================================================
                        # CORRECTED REPORT LOGIC - MOVED INSIDE THE SUCCESS BLOCK
                        # This now runs for each successfully processed payload.
                        # ==================================================================
                        try:
                            # Use .get() for safe access from the payload that was just sent
                            asn_id = payload_to_send.get('AsnId')
                            origin_facility = payload_to_send.get('OriginFacilityId')
                            lpn_list = payload_to_send.get('Lpn', [])  # Default to empty list
                            carrier_id = payload_to_send.get('CarrierId')
                            collected_asn.append(asn_id)

                            for lpn in lpn_list:
                                lpn_id = lpn.get('LpnId')
                                collected_lpn.append(lpn_id)
                                if lpn.get('LpnDetail'):
                                    item_id = lpn['LpnDetail'][0].get('ItemId')
                                    quantity = lpn['LpnDetail'][0].get('ShippedQuantity')

                                    report_entry = {
                                        "PLANT": plant_id,
                                        "ENVN": environment,
                                        "ASN_ID": asn_id,
                                        "LPN_ID": lpn_id,
                                        "ITEM_ID": item_id,
                                        "QTY": quantity,
                                        "O_FACILITY": origin_facility,
                                        "CARRIER": carrier_id
                                    }
                                    extracted_report_data.append(report_entry)

                        except (TypeError, ValueError, KeyError) as e:
                            print(
                                f"--> WARNING: Could not parse report data from successful payload. Malformed data? Error: {e}")

                    except KeyError as e:
                        print(f"--> ERROR: Could not process payload {i + 1}. Data is malformed. Missing key: {e}")
                    except requests.exceptions.RequestException as e:
                        print(f"--> ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            print(f"--> Status Code: {e.response.status_code}, Response: {e.response.text}")
                    except Exception as e:
                        print(f"--> ERROR: An unexpected error occurred for payload {i + 1}: {e}")

                    formatted_lpn = ';'.join(collected_lpn)
                    formatted_asn = ';'.join(collected_asn)
                    output_file = {
                        "PLANT": plant_id,
                        "ENVN": environment,
                        "ASN_ID": formatted_asn,
                        "LPN_ID": formatted_lpn,
                        "Pre_Allocate": "Y"
                    }
                    output_data.append(output_file)

            except Exception as e:
                print(f"--> FATAL ERROR: Could not process batch for environment {environment.upper()}. Error: {e}")

        # 12. Generate the final report from ALL collected data
        if extracted_report_data:
            print("\n" + "=" * 25 + " Generating Report " + "=" * 25)
            try:
                report_df = pd.DataFrame(extracted_report_data)

                # Define the Output path.
                output_dir = Path("Output_files")
                output_dir.mkdir(parents=True, exist_ok=True)  # Just safe guaring.
                output_filepath = output_dir / "ASN_Creation_Report.xlsx"

                report_df.to_excel(output_filepath, index=False)
                print(f"Successfully created report: {output_filepath}")
            except Exception as e:
                print(f"--> ERROR: Failed to create Excel report. Error: {e}")
        else:
            print("\nNo data was successfully processed to generate a report.")

        if output_data:
            print("\n" + "=" * 25 + " Generating input sheet from the create ASN output " + "=" * 25)
            try:

                report_df = pd.DataFrame(output_file, index=[0])

                output_dir = Path("Input_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / "WorkSheet1.xlsx"

                # Use ExcelWriter to write to multiple sheets in the same file
                with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
                    # Rename columns to match the expected format for each sheet
                    # This is a crucial step for making the output file usable by other processes

                    # For SearchASN, InboundDelivery, ASNVerify
                    asn_df = report_df.rename(columns={"PLANT": "Plant", "ENVN": "Environment", "ASN_ID": "ASNID", "LPN_ID": "LPNID", "Pre_Allocate": 'Pre_Allocate'})
                    asn_df.to_excel(writer, sheet_name='SearchASN', index=False)
                    asn_df.to_excel(writer, sheet_name='InboundDelivery', index=False)
                    asn_df.to_excel(writer, sheet_name='ASNVerify', index=False)
                    asn_df.to_excel(writer, sheet_name='GoodsHolderAnnounced', index=False)
                    asn_df.to_excel(writer, sheet_name='GoodsHolderWeighed', index=False)
                    asn_df.to_excel(writer, sheet_name='PutawayTaskComplete', index=False)
                    asn_df.to_excel(writer, sheet_name='ASNVerify', index=False)

                print(f"Successfully created multi-sheet report: {output_filepath}")

            except Exception as e:
                print(f"--> ERROR: Failed to create multi-sheet Excel report. Error: {e}")

        else:
            print("\nNo data was successfully processed to generate an input sheet.")


asn_create = ASN_Creation()
asn_create.create_asns()
