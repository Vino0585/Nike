import requests
from collections import defaultdict
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Payload_generation.Putaway_Complete_Payload import Payload_Complete_Payload

class Putaway_Complete:

    def create_putaway_task_complete(self):
        ptwy_instance = Payload_Complete_Payload()
        # ptwy means putaway task complete
        raw_payloads = ptwy_instance.create_putaway_complete_payloads()
        if not raw_payloads:
            print("No Putaway Completed Payload Found")
            return None

        # Group payloads by both environment and plant to ensure correct token and URL are used for each.
        payloads_by_group = defaultdict(list)
        for package in raw_payloads:
            # The payload source returns dictionaries directly, so no JSON parsing is needed.
            # We'll just ensure the package is a dictionary before proceeding.
            if not isinstance(package, dict):
                print(f"--> WARNING: Skipping package as it's not a valid dictionary: {package}")
                continue

            env = package.get('environment')
            plant_id = package.get('plant')
            payload = package.get('PTWYCPayload')

            if env and plant_id and payload:
                payloads_by_group[(env, plant_id)].append(payload)
            else:
                print(f"--> WARNING: Skipping malformed package: {package}")

        env_handler = AWM_Env()  # Instantiate once outside the loop

        response_result = []
        for (environment, plant_id), payloads in payloads_by_group.items():
            print(
                f"\n{'=' * 20} Processing {len(payloads)} Payloads for Env: {environment.upper()} / Plant: {plant_id} {'=' * 20}")
            try:
                # Get token ONCE for this specific environment and plant combination
                token_handler = Get_Token(env=environment.lower(), plant=plant_id)
                bearer_token = token_handler.get_bearer()
                print(f"Successfully retrieved token for {environment.upper()} env, Plant {plant_id}.")

                # Get URL ONCE for this group
                env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
                # Hardcode the program name for reliability, fixing the issue where it resolves incorrectly.
                api_url = env_handler.get_program_url(program="Putaway_Task_Complete")
                print(f"Sending payloads to URL: {api_url}")

                headers = {
                    "content-type": "application/json",
                    "selectedorganization": str(plant_id),
                    "selectedlocation": str(plant_id),
                    "authorization": f'Bearer {bearer_token}'
                }

                for i, payload_to_send in enumerate(payloads):
                    try:
                        print(f"\n--- [{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} ---")
                        response = requests.post(url=api_url, headers=headers, json=payload_to_send)
                        response.raise_for_status()
                        response_data = response.json()
                        response_result.append(response_data.get('success'))
                        print(f"--> SUCCESS: Payload {i + 1} processed successfully.")

                    except requests.exceptions.JSONDecodeError:
                        print(f"--> ERROR: Failed to decode JSON from response for payload {i + 1}.")
                        print(f"--> Raw Response Text: {response.text}")
                    except requests.exceptions.RequestException as e:
                        print(f"--> ERROR: API request failed for payload {i + 1}: {e}")
                        if e.response is not None:
                            print(f"--> API Response Body: {e.response.text}")
                    except Exception as e:
                        print(f"--> ERROR: An unexpected error occurred for payload {i + 1}: {e}")
            except Exception as e:
                print(
                    f"--> FATAL ERROR: Could not process batch for env {environment.upper()}/plant {plant_id}. Error: {e}")

        print(f"\n{'=' * 25} Processing Finished {'=' * 25}")
        print(f"Total of {len(response_result)} payloads were sent successfully.")


# ptwy_complete = Putaway_Complete()
# ptwy_complete.create_putaway_task_complete()