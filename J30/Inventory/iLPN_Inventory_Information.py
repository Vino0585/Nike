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


def iLPN_search():
    # 1. Create an instance of the generator and assigning the function to variable.
    ilpn_payload = iLPN_Search_Payload()

    iLPN_receiving_payload = ilpn_payload.create_lpn_receiving_payload()
    iLPN_inventory_payload = ilpn_payload.create_lpn_inventory_payload()
    bearer_token = ''
    env_handler = AWM_Env()
    all_ilpn_receiving_data = []
    all_ilpn_inventory_data = []

    if not iLPN_receiving_payload and not iLPN_inventory_payload:
        logging.error("No payloads were generated. Please check your Excel input and generator logic.")
        return

    payload_by_env = defaultdict(list)
    for payload in iLPN_receiving_payload:
        env = payload.get('envn')
        plant_id = payload.get('plant')
        payload_to_send = payload.get('payload')
        if env and plant_id and payload_to_send:
            payload_by_env[env].append({'plant': plant_id, 'payload': payload_to_send})
        else:
            logging.error(f"--> WARNING: Skipping malformed package: {payload}")
            continue

    for environment, packaged_payloads in payload_by_env.items():
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
                                'Environment': environment.upper(),
                                'Plant': plant_id,
                                'ASN_ID': response_payload.get('AsnId'),
                                'iLPN_ID': response_payload.get('LpnId'),
                                'LpnStatus': response_payload.get('LpnStatus'),
                                'DiversionCodeId': response_payload.get('DiversionCodeId'),
                                'PreReceiptStatusId': response_payload.get('PreReceiptStatusId'),
                                'ItemID': lpn_detail.get('ItemId'),
                                'Qty': lpn_detail.get('ShippedQuantity'),
                                'InventoryAttribute1': lpn_detail.get('InventoryAttribute1'),
                                'PO_NBR': lpn_detail.get('PurchaseOrderId'),
                                'UpdatedBy': lpn_detail.get('UpdatedBy')
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

        payload_by_env = defaultdict(list)
        for payload in iLPN_inventory_payload:
            env = payload.get('envn')
            plant_id = payload.get('plant')
            payload_to_send = payload.get('payload')
            if env and plant_id and payload_to_send:
                payload_by_env[env].append({'plant': plant_id, 'payload': payload_to_send})
            else:
                logging.error(f"--> WARNING: Skipping malformed package: {payload}")
                continue

        for environment, packaged_payloads in payload_by_env.items():
            logging.info(f"Processing {len(packaged_payloads)} Payloads for Environment: {environment.upper()}")
            try:
                plant_id = packaged_payloads[0].get('plant')
                # 5. Already got the bearer token and stored in the variable.

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
                                'Environment': environment.upper(),
                                'Plant': plant_id,
                                'ASN_ID': response_payload.get('AsnId'),
                                'iLPN_ID': response_payload.get('IlpnId'),
                                'IB_Delivery': response_payload.get('ShipmentId'),
                                'iLPN_Status': response_payload.get('Status'),
                                'ItemID': response_payload.get('ItemId'),
                                'Single_Line_LPN': response_payload.get('SingleLineLpn'),
                                'Height': response_payload.get('Height'),
                                'Width': response_payload.get('Width'),
                                'Length': response_payload.get('Length'),
                                'Actual_Weight': response_payload.get('ActualWeight'),
                                'Volume': response_payload.get('Volume'),
                                'PO_NBR': response_payload.get('PurchaseOrderId'),
                                'Previous_Location': response_payload.get('PreviousLocationId'),
                                'Current_Location': response_payload.get('CurrentLocationId'),
                                'Destination_Location': response_payload.get('DestinationLocationId')
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

        # 1. Print the results to the console in a clean table format
        print(result_receiving_df.to_string(index=False))
        print(result_inventory_df.to_string(index=False))

        # 2. Export the DataFrame to an Excel file (Improved Path Handling)
        # Create a Path object for the output directory.
        output_dir = Path("../Output_files")
        # Check if directory exist.
        output_dir.mkdir(parents=True, exist_ok=True)
        # Define the full path to the output file.
        output_filepath = output_dir / "iLPN_search_results.xlsx"

        report_df = pd.DataFrame(result_receiving_df)
        with pd.ExcelWriter(output_filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            result_receiving_df.to_excel(writer, sheet_name='iLPN_Receiving_Result', index=False)
            result_inventory_df.to_excel(writer, sheet_name='iLPN_Inventory_Result', index=False)

        logging.info(
            f"Successfully exported {len(all_ilpn_receiving_data)} and {len(all_ilpn_inventory_data)} results to '{output_filepath}'")

    except Exception as e:
        logging.error(f"ERROR: Failed to generate or export the final report: {e}")


if __name__ == "__main__":
    iLPN_search()
