from pathlib import Path
import requests
import json
from collections import defaultdict
from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Payload_generation.Goods_Holder_Payload import Goods_Holder


def create_goods_holder_announced():
    gha_instance = Goods_Holder()
    # gha means goods holder announced
    raw_payloads = gha_instance.create_goods_holder_announced_payloads()
    if not raw_payloads:
        print("No Goods Holder Announced Payload Found")
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
        payload = package.get('GHAPayload')

        if env and plant_id and payload:
            payloads_by_group[(env, plant_id)].append(payload)
        else:
            print(f"--> WARNING: Skipping malformed package: {package}")

    env_handler = AWM_Env()  # Instantiate once outside the loop

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
            api_url = env_handler.get_program_url(program="Goods_Holder_Announced")
            print(f"Sending payloads to URL: {api_url}")

            headers = {
                "content-type": "application/json",
                "organization": str(plant_id),
                "location": str(plant_id),
                "authorization": f'Bearer {bearer_token}'
            }

            for i, payload_to_send in enumerate(payloads):
                try:
                    # print(json.dumps(payload_to_send, indent=2))
                    print(f"\n--- [{environment.upper()}] Processing Payload {i + 1}/{len(payloads)} ---")
                    for payload in payload_to_send:
                        response = requests.post(url=api_url, headers=headers, json=payload)
                        response.raise_for_status()

                        response_data = response.json()
                        print(
                            f"-> Success: {response_data.get('success', 'N/A')}, Message: {response_data.get('messageKey', 'No message key')}")
                except KeyError as e:
                    print(f"--> ERROR: Could not process payload {i + 1}. Data is malformed. Missing key: {e}")
                except requests.exceptions.RequestException as e:
                    print(f"--> ERROR: API request failed for payload {i + 1}: {e}")
                    if e.response is not None:
                        print(f"--> Status Code: {e.response.status_code}, Response: {e.response.text}")
                except Exception as e:
                    print(f"--> ERROR: An unexpected error occurred for payload {i + 1}: {e}")
        except Exception as e:
            print(
                f"--> FATAL ERROR: Could not process batch for env {environment.upper()}/plant {plant_id}. Error: {e}")


if __name__ == "__main__":
    create_goods_holder_announced()