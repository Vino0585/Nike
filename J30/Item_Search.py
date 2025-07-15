import pandas as pd
from J30.Environment.Get_Token import Get_Token
from J30.Payload_generation.Item_Search_Payload import ItemPayload
from collections import defaultdict
from J30.Environment.WM_Environment import AWM_Env
import requests
from pathlib import Path

def item_search():
    # 1. Create an instance of the generator
    item_payload_gen = ItemPayload()

    # 2. Generate the list from item payload.
    item_payload_package = item_payload_gen.create_item_search_payloads()
    if not item_payload_package:
        print("\nNo payloads were generated. Please check your Excel input and generator logic.")
        return

    # 3. Group payloads by their target environment (Corrected Logic)
    payloads_by_env = defaultdict(list)
    for package in item_payload_package:
        env = package.get('envn')
        plant_id = package.get('plant')
        payload = package.get('payload')
        if env and plant_id and payload:
            payloads_by_env[env].append({'plant': plant_id, 'payload': payload})
        else:
            print(f"--> WARNING: Skipping malformed package: {package}")
            continue

    # This list will hold all results from all API calls
    all_results_data = []

    # 4. Loop through each environment group and process its payloads
    for environment, packaged_payloads in payloads_by_env.items():
        print(f"\n{'=' * 20} Processing {len(packaged_payloads)} Payloads for Environment: {environment.upper()} {'=' * 20}")
        try:
            plant_id = packaged_payloads[0].get('plant')
            # 5. Get token ONCE for the entire environment batch
            token_handler = Get_Token(environment.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()
            if not bearer_token:
                print(f"--> FATAL: Could not get token for {environment.upper()}. Skipping this environment.")
                continue
            print(f"Successfully retrieved token for {environment.upper()} environment.")

            env_handler = AWM_Env()

            # 6. Now loop through the individual payloads for this environment
            for i, item in enumerate(packaged_payloads):
                try:
                    # 7. Unpack the plant_id and payload for this specific request
                    plant_id = item['plant']
                    payload_to_send = item['payload']

                    print(f"\n--- [{environment.upper()}] Processing Payload {i + 1}/{len(packaged_payloads)} for Plant {plant_id} ---")

                    # 8. Get URL for THIS payload's specific plant
                    env_handler.get_wm_host(host=environment.lower(), facility=str(plant_id))
                    url_value = env_handler.get_program_url(program=Path(__file__).stem)
                    print(f"Sending payload to URL: {url_value}")

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

                    # 11. Process and collect the results from the response
                    item_list = response_data.get('data', [])
                    if not item_list:
                        print("-> Success, but no items were returned in the response.")
                        continue

                    print(f"-> Success: Found {len(item_list)} item(s) in response.")
                    for response_payload in item_list:
                        extended_data = response_payload.get('Extended', {})
                        result_row = {
                            'Environment': environment.upper(),
                            'Plant': plant_id,
                            'ItemId': response_payload.get('ItemId'),
                            'Length': response_payload.get('Length'),
                            'Height': response_payload.get('Height'),
                            'Width': response_payload.get('Width'),
                            "DimsUOM": response_payload.get('DimensionUomId'),
                            'Volume': response_payload.get('Volume'),
                            'VolumeUOM': response_payload.get('VolumeUomId'),
                            'Weight': response_payload.get('Weight'),
                            'WeightUOM': response_payload.get('WeightUomId'),
                            'PrimaryBarCode': response_payload.get('PrimaryBarCode'),
                            'DivisionCode': extended_data.get('DivisionCode'),
                            'MarkforCubiScan': extended_data.get('MarkForCubiscan')
                        }
                        all_results_data.append(result_row)

                except (KeyError, TypeError) as e:
                    print(f"--> ERROR: Could not process payload {i + 1}. Data malformed. Details: {e}")
                except requests.exceptions.RequestException as e:
                    print(f"--> ERROR: API request failed for payload {i + 1}: {e}")
                    if e.response is not None:
                        print(f"--> Status Code: {e.response.status_code}, Response: {e.response.text}")
                except Exception as e:
                    print(f"--> ERROR: An unexpected error occurred for payload {i + 1}: {e}")

        except Exception as e:
            print(f"--> FATAL: Could not process batch for environment {environment.upper()}. Error: {e}")

    # --- Final Step: Process all collected results after the loops are done ---
    # --- Final Step: Process all collected results after the loops are done ---
    if not all_results_data:
        print("\n--- Script finished, but no results were collected from any API calls. ---")
        return

    print(f"\n{'=' * 25} Consolidated Search Results {'=' * 25}")
    try:
        # Create a pandas DataFrame from the list of result dictionaries
        results_df = pd.DataFrame(all_results_data)
        # Clean up data types for better presentation
        results_df['Length'] = pd.to_numeric(results_df['Length'], errors='coerce').fillna(0)

        # 1. Print the results to the console in a clean table format
        print(results_df.to_string(index=False))

        # 2. Export the DataFrame to an Excel file (Improved Path Handling)
        # Create a Path object for the output directory.
        output_dir = Path("Output_files")
        # Check if directory exist.
        output_dir.mkdir(parents=True, exist_ok=True)
        # Define the full path to the output file.
        output_filepath = output_dir / "item_search_results.xlsx"
        results_df.to_excel(output_filepath, sheet_name='ItemSearchResult', index=False)

        print(f"\n-> Successfully exported {len(results_df)} results to '{output_filepath}'")
        # --- End of suggested change ---

    except Exception as e:
        print(f"\n--> ERROR: Failed to generate or export the final report: {e}")

if __name__ == "__main__":
    item_search()