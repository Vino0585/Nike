import pandas as pd
import requests
import logging

from collections import defaultdict
from Inventory.Inventory_Payload_Generation.iLPN_Information_Payloads import iLPN_Search_Payload
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from pathlib import Path

# Set up Logging level and format.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class iLPN_Search:

    def iLPN_query(self):
        # 1. Create an instance of the generator and assigning the function to variable.
        ilpn_payload = iLPN_Search_Payload()

        iLPN_receiving_payload = ilpn_payload.create_lpn_receiving_payload()
        iLPN_inventory_payload = ilpn_payload.create_lpn_inventory_payload()
        iLPN_condition_code_payload = ilpn_payload.create_ilpn_condition_code_payload()
        bearer_token = ''
        env_handler = AWM_Env()
        all_ilpn_receiving_data = []
        all_ilpn_inventory_data = []
        all_ilpn_condition_code_data = []

        if not iLPN_receiving_payload and not iLPN_inventory_payload:
            logging.error("No payloads were generated. Please check your Excel input and generator logic.")
            return

        receiving_payload_by_env = defaultdict(list)
        for payload in iLPN_receiving_payload:
            env = payload.get('envn')
            plant_id = payload.get('plant')
            payload_to_send = payload.get('payload')
            if env and plant_id and payload_to_send:
                receiving_payload_by_env[env].append({'plant': plant_id, 'payload': payload_to_send})
            else:
                logging.error(f"--> WARNING: Skipping malformed package: {payload}")
                continue

        for environment, packaged_payloads in receiving_payload_by_env.items():
            logging.info(f"Processing {len(packaged_payloads)} Payloads for Environment: {environment.upper()}")
            try:
                plant_id = packaged_payloads[0].get('plant')
                # 5. Get token once for the entire environment batch
                token_handler = Get_Token(environment.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                if not bearer_token:
                    logging.error(f"--> FATAL: Could not get token for {environment.upper()}. Skipping this environment.")
                    continue
                logging.info(f"Successfully retrieved token for {environment.upper()} environment.")

                env_handler = AWM_Env()

                # 6. Now loop through the individual payloads for this environment
                for i, item in enumerate(packaged_payloads):
                    try:

                        # 7. Unpack the plant_id and payload for this specific request
                        plant_id = item['plant']
                        payload_to_send = item['payload']

                        logging.info(
                            f"[{environment.upper()}] Processing Payload {i + 1}/{len(packaged_payloads)} for Plant {plant_id}")

                        # 8. Get URL for this payloads specific plant
                        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
                        url_value = env_handler.get_program_url(program='iLPN_Receiving')
                        logging.info(f"Sending payload to URL: {url_value}")

                        # 9. Build headers
                        headers = {
                            "content-type": "application/json",
                            "organization": str(plant_id),
                            "location": str(plant_id),
                            "authorization": 'Bearer ' + bearer_token
                        }

                        # 10. Send the request
                        response = requests.post(url=url_value, headers=headers, json=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()

                        # 11. Process and collect the result from the response.
                        ilpn_list = response_data.get('data', [])
                        if not ilpn_list:
                            logging.info("-> Success, but no ilpn were returned in the response.")
                            continue

                        logging.info(f"-> Success: Found {len(ilpn_list)} iLPN(s) in response.")
                        for response_payload in ilpn_list:
                            lpn_detail = response_payload.get('LpnDetail', [])
                            for lpn_detail in lpn_detail:
                                result_row = {
                                    'ENVN': environment.upper(),
                                    'Plant': plant_id,
                                    'ASN_ID': response_payload.get('AsnId'),
                                    'iLPN_ID': response_payload.get('LpnId'),
                                    'LpnStat': response_payload.get('LpnStatus'),
                                    'Diversion': response_payload.get('DiversionCodeId'),
                                    'PreRecptStatId': response_payload.get('PreReceiptStatusId'),
                                    'ItemID': lpn_detail.get('ItemId'),
                                    'Qty': lpn_detail.get('ShippedQuantity'),
                                    'Invn_Attri_1': lpn_detail.get('InventoryAttribute1'),
                                    'PO_NBR': lpn_detail.get('PurchaseOrderId'),
                                    'User': lpn_detail.get('UpdatedBy')
                                }
                                all_ilpn_receiving_data.append(result_row)

                    except (KeyError, TypeError) as e:
                        logging.error(f"ERROR: Could not process payload {i + 1}. Data malformed. Details: {e}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
                    except Exception as e:
                        logging.error(f"An unexpected error occurred for payload {i + 1}: {e}")

            except Exception as e:
                logging.error(f"FATAL: Could not process batch for environment {environment.upper()}. Error: {e}")

        inventory_payload_by_env = defaultdict(list)
        for payload in iLPN_inventory_payload:
            env = payload.get('envn')
            plant_id = payload.get('plant')
            payload_to_send = payload.get('payload')
            if env and plant_id and payload_to_send:
                inventory_payload_by_env[env].append({'plant': plant_id, 'payload': payload_to_send})
            else:
                logging.error(f"--> WARNING: Skipping malformed package: {payload}")
                continue

        for environment, packaged_payloads in inventory_payload_by_env.items():
            logging.info(f"Processing {len(packaged_payloads)} Payloads for Environment: {environment.upper()}")
            try:
                plant_id = packaged_payloads[0].get('plant')

                # 6. Now loop through the individual payloads for this environment
                for i, item in enumerate(packaged_payloads):
                    try:
                        # 7. Unpack the plant_id and payload for this specific request
                        plant_id = item['plant']
                        payload_to_send = item['payload']

                        logging.info(
                            f"[{environment.upper()}] Processing Payload {i + 1}/{len(packaged_payloads)} for Plant {plant_id}")

                        # 8. Get URL for this payloads specific plant
                        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
                        url_value = env_handler.get_program_url(program='iLPN_Inventory')
                        logging.info(f"Sending payload to URL: {url_value}")

                        # 9. Build headers
                        headers = {
                            "content-type": "application/json",
                            "organization": str(plant_id),
                            "location": str(plant_id),
                            "authorization": 'Bearer ' + bearer_token
                        }

                        # 10. Send the request
                        response = requests.post(url=url_value, headers=headers, json=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()

                        # 11. Process and collect the result from the response.
                        ilpn_list = response_data.get('data', [])
                        if not ilpn_list:
                            logging.info("-> Success, but no ilpn were returned in the response.")
                            continue

                        logging.info(f"-> Success: Found {len(ilpn_list)} iLPN(s) in response.")
                        for response_payload in ilpn_list:
                            result_row = {
                                'ENVN': environment.upper(),
                                'Plant': plant_id,
                                'ASN_ID': response_payload.get('AsnId'),
                                'iLPN_ID': response_payload.get('IlpnId'),
                                'IB_Delivery': response_payload.get('ShipmentId'),
                                'iLPN_Status': response_payload.get('Status'),
                                'ItemID': response_payload.get('ItemId'),
                                'Single_SKU': response_payload.get('SingleLineLpn'),
                                'H': response_payload.get('Height'),
                                'W': response_payload.get('Width'),
                                'L': response_payload.get('Length'),
                                'Weight': response_payload.get('ActualWeight'),
                                'Volume': response_payload.get('Volume'),
                                'PO_NBR': response_payload.get('PurchaseOrderId'),
                                'Prev_Locn': response_payload.get('PreviousLocationId'),
                                'Curr_Locn': response_payload.get('CurrentLocationId'),
                                'Dest_Locn': response_payload.get('DestinationLocationId')
                            }
                            all_ilpn_inventory_data.append(result_row)

                    except (KeyError, TypeError) as e:
                        logging.error(f"ERROR: Could not process payload {i + 1}. Data malformed. Details: {e}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
                    except Exception as e:
                        logging.error(f"An unexpected error occurred for payload {i + 1}: {e}")

            except Exception as e:
                logging.error(f"FATAL: Could not process batch for environment {environment.upper()}. Error: {e}")


        condition_code_payload_by_env = defaultdict(list)
        for payload in iLPN_condition_code_payload:
            env = payload.get('envn')
            plant_id = payload.get('plant')
            payload_to_send = payload.get('payload')
            if env and plant_id and payload_to_send:
                condition_code_payload_by_env[env].append({'plant': plant_id, 'payload': payload_to_send})
            else:
                logging.error(f"--> WARNING: Skipping malformed package: {payload}")
                continue

        for environment, packaged_payloads in condition_code_payload_by_env.items():
            logging.info(f"Processing {len(packaged_payloads)} Payloads for Environment: {environment.upper()}")
            try:
                for i, item in enumerate(packaged_payloads):
                    try:
                        # 7. Unpack the plant_id and payload for this specific request
                        plant_id = item['plant']
                        payload_to_send = item['payload']

                        logging.info(
                            f"[{environment.upper()}] Processing Payload {i + 1}/{len(packaged_payloads)} for Plant {plant_id}")

                        # 8. Get URL for this payloads specific plant
                        env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
                        url_value = env_handler.get_program_url(program='iLPN_Condition_Code')
                        logging.info(f"Sending payload to URL: {url_value}")

                        # 9. Build headers
                        headers = {
                            "content-type": "application/json",
                            "organization": str(plant_id),
                            "location": str(plant_id),
                            "authorization": 'Bearer ' + bearer_token
                        }

                        # 10. Send the request
                        response = requests.post(url=url_value, headers=headers, json=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()

                        # 11. Process and collect the result from the response.
                        ilpn_list = response_data.get('data', [])
                        if not ilpn_list:
                            logging.info("-> Success, but no ilpn were returned in the response.")
                            continue

                        logging.info(f"-> Success: Found {len(ilpn_list)} iLPN(s) in response.")
                        for response_payload in ilpn_list:
                            lpn = response_payload.get('Ilpn', {})
                            if not lpn:
                                logging.warning(f"Skipping result, 'Ilpn' dictionary is missing or empty in response: {response_payload}")
                                continue
                            inventory = response_payload.get('Inventory', {})
                            if not inventory:
                                logging.warning(f"Skipping result, 'Inventory' dictionary is missing or empty in response: {response_payload}")
                                continue

                            condition_code_result_row = {
                                'ENVN': environment.upper(),
                                'Plant': plant_id,
                                'ASN_ID': lpn.get('AsnId'),
                                'iLPN_ID': lpn.get('IlpnId'),
                                'ItemID': lpn.get('ItemId'),
                                'Source_LPN': lpn.get('SourceLpnId'),
                                'Qty': inventory.get('OnHand'),
                                'Condition_Code_type': response_payload.get('ConditionContainerDesc'),
                                'Condition_Code_Desc': response_payload.get('ConditionCodeDescription'),
                                'UserId': response_payload.get('UpdatedBy'),
                                'Status': response_payload.get('IlpnStatusDescription'),
                                'Barcode': inventory.get('PrimaryBarCode')
                            }
                            all_ilpn_condition_code_data.append(condition_code_result_row)

                    except (KeyError, TypeError) as e:
                        logging.error(f"ERROR: Could not process payload {i + 1}. Data malformed. Details: {e}")
                    except requests.exceptions.RequestException as e:
                        logging.error(f"ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            logging.error(f"Status Code: {e.response.status_code}, Response: {e.response.text}")
                    except Exception as e:
                        logging.error(f"An unexpected error occurred for payload {i + 1}: {e}")

            except Exception as e:
                logging.error(f"FATAL: Could not process batch for environment {environment.upper()}. Error: {e}")

        # --- Final Step: Process all collected results after the loops are done ---

        if not all_ilpn_receiving_data:
            logging.info("Script finished, but no results were collected from API call made to iLPN Receiving")
            return

        if not all_ilpn_inventory_data:
            logging.info("Script finished, but no results were collected from API call made to iLPN Inventory")
            return

        logging.info(f"Consolidated Search Results")
        try:
            # Create a pandas DataFrame from the list of result dictionaries
            result_receiving_df = pd.DataFrame(all_ilpn_receiving_data)
            result_inventory_df = pd.DataFrame(all_ilpn_inventory_data)
            result_condition_df = pd.DataFrame(all_ilpn_condition_code_data)

            # Sort the DataFrames for consistent and readable output.
            if not result_receiving_df.empty:
                result_receiving_df = result_receiving_df.sort_values(by=['ASN_ID', 'ItemID'])
            if not result_inventory_df.empty:
                result_inventory_df = result_inventory_df.sort_values(by=['ASN_ID', 'ItemID'])
            if not result_condition_df.empty:
                result_condition_df = result_condition_df.sort_values(by=['ASN_ID', 'iLPN_ID', 'ItemID'])

            # 1. Print the results to the console in a clean table format
            if not result_receiving_df.empty:
                print(result_receiving_df.to_string(index=False))
            if not result_inventory_df.empty:
                print(result_inventory_df.to_string(index=False))
            if not result_condition_df.empty:
                print(result_condition_df.to_string(index=False))


            # 2. Export the DataFrame to an Excel file (Improved Path Handling)
            output_dir = Path("../Output_files")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filepath = output_dir / "iLPN_search_results.xlsx"

            with pd.ExcelWriter(output_filepath, engine='openpyxl') as writer:
                result_receiving_df.to_excel(writer, sheet_name='iLPN_Receiving_Result', index=False)
                result_inventory_df.to_excel(writer, sheet_name='iLPN_Inventory_Result', index=False)
                result_condition_df.to_excel(writer, sheet_name='iLPN_Condition_Result', index=False)

            logging.info(
                f"Successfully exported {len(all_ilpn_receiving_data)} and {len(all_ilpn_inventory_data)} results to '{output_filepath}'")

        except Exception as e:
            logging.error(f"Failed to generate or export the final report: {e}")

if __name__ == "__main__":
    query = iLPN_Search()
    query.iLPN_query()