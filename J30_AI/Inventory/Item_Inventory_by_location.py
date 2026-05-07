import pandas as pd
import requests
import logging

from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Inventory.Inventory_Payload_Generation.iLPN_Information_Payloads import iLPN_Search_Payload

# Set up Logging level and format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Item_Inventory_By_Location:

    def item_inventory_by_location(self):
        # Create an instance of the generator and assigning the function to variable.
        item_payload = iLPN_Search_Payload()

        item_inventory_payload = item_payload.create_item_inventory_by_location_payload()

        if not item_inventory_payload:
            logging.error("No payloads were generated. Please check your payload generator logic and excel"
                          " input and generator logic.")
            return

        #1. Get all variables from payload

        env = item_inventory_payload['envn']
        plant_id = item_inventory_payload['plant']
        payload_to_send = item_inventory_payload['payload']

        if not (env and plant_id and payload_to_send):
            logging.error(f"--> WARNING: Skipping malformed package: {item_inventory_payload}")
            return

        get_result = []
        try:
            # 2. Get token once for the entire environment batch
            token_handler = Get_Token(env.lower(), plant=plant_id)
            bearer_token = token_handler.get_bearer()
            if not bearer_token:
                logging.error(f"--> FATAL: Could not get token for {env.upper()}. "
                              f"Skipping this environment.")
                return
            logging.info(f"Successfully retrieved token for {env.upper()} environment.")

            env_handler = AWM_Env()

            # 3. Get URL for this payloads specific plant
            env_handler.get_wm_host(host=env.lower(), facility=str(plant_id))
            url_value = env_handler.get_program_url(program='Item_Inventory_By_Location')
            logging.info(f"Sending payload to URL: {url_value}")

            # 4. Build headers
            headers = {
                "content-type": "application/json",
                "organization": str(plant_id),
                "location": str(plant_id),
                "authorization": 'Bearer ' + bearer_token
            }

            response_data = []
            for payload in payload_to_send:
                # 5. Send the request
                response = requests.post(url=url_value, headers=headers, json=payload)
                response.raise_for_status()
                response_data.append(response.json())
                extracted_data = response_data[0]['data']['Results']
                get_result = item_payload.extract_item_inventory_by_location(extracted_data)

        except Exception as e:
            logging.error(f"--> FATAL: {e}")
            return None

        # --- Final Step: Process all collected results after the loops are done ---
        if not get_result:
            logging.error('The payload did not give any result thats why the parsing also is null check your payload')
            return None
        try:
            result_df = pd.DataFrame(get_result)
            print(result_df.to_string(index=False))
        except Exception as e:
            print(f"\n--> ERROR: Failed to generate or export the final report: {e}")

if __name__ == "__main__":
    response = Item_Inventory_By_Location()
    from pprint import pprint
    pprint(response.item_inventory_by_location())