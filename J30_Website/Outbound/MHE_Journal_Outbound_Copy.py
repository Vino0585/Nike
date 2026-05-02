import json
import logging
from io import BytesIO
from pathlib import Path
import sys

import pandas as pd
import requests

# Ensure project root is on sys.path so package imports resolve when run via Streamlit.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Environment.Get_Token import Get_Token
from Environment.WM_Environment import AWM_Env
from Outbound.Outbound_Payload_Generation.Task_Detail_Search import Task_Search_Payload


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class MHEJournalOutboundCopy:
    """Wave-driven copy of MHE journal outbound processing for Streamlit use."""

    def __init__(self):
        self.task_search = Task_Search_Payload()

    @staticmethod
    def _build_message_journal_payload(lpn: str, message_type: str) -> dict:
        return {
            "ViewName": "MessageJournal",
            "Filters": [
                {"AttributeId": "MessageType", "FilterValues": [message_type]},
                {
                    "AttributeId": "Stage1.MessagePayload",
                    "FilterValues": [lpn],
                    "negativeFilter": False,
                },
            ],
            "TimeZone": "Japan",
            "ComponentName": "com-manh-cp-dmui-search",
        }

    def _build_wave_payloads(self, wave_number: str, environment: str, plant_id: str) -> tuple[list, list]:
        task_details = self.task_search.search_task_detail_by_wave_nbr(
            search_by_wave_nbr=wave_number,
            environment=environment,
            plant_id=plant_id,
        )

        iLPNs = task_details.get("iLPN", [])
        oLPNs = task_details.get("oLPN", [])

        ilpn_message_types = [
            "PPK_DEI_TaskRelease",
            "RetrievalTaskResult",
            "RoutingTaskResult",
            "PTW_DEI_AllocationCreated",
            "ReplenTaskResult ",
            "PackTaskResult",
            "GoodsholderDivertedDueToException",
            "Pack_Complete",
        ]
        olpn_message_types = [
            "PPK_DEI_TaskRelease",
            "PickTaskResult",
            "Pack_Complete",
            "GoodsholderMeasured",
            "RoutingTaskResult",
        ]

        ilpn_payloads = [
            self._build_message_journal_payload(lpn, message)
            for lpn in iLPNs
            for message in ilpn_message_types
        ]
        olpn_payloads = [
            self._build_message_journal_payload(lpn, message)
            for lpn in oLPNs
            for message in olpn_message_types
        ]
        return ilpn_payloads, olpn_payloads

    @staticmethod
    def _get_api_context(environment: str, plant_id: str) -> tuple[str, dict]:
        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()

        env_handler = AWM_Env()
        env_handler.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = env_handler.get_program_url(program="Message_Journal_Inbound")

        headers = {
            "content-type": "application/json",
            "selectedorganization": str(plant_id),
            "selectedlocation": str(plant_id),
            "authorization": f"Bearer {bearer_token}",
        }
        return api_url, headers

    def _collect_ilpn_results(self, payloads: list, environment: str, plant_id: str) -> pd.DataFrame:
        api_url, headers = self._get_api_context(environment, plant_id)
        rows = []

        for index, payload in enumerate(payloads, start=1):
            try:
                logging.info("[iLPN] Processing payload %s/%s", index, len(payloads))
                response = requests.post(url=api_url, headers=headers, json=payload)
                response.raise_for_status()
                results = response.json().get("data", {}).get("Results", [])

                for entry in results:
                    header_info = entry.get("headers", {})
                    message_payload_str = entry.get("Stage1", {}).get("MessagePayload", "{}")
                    message_payload = json.loads(message_payload_str)
                    event = message_payload.get("event", {}).get("type") or message_payload.get("MessageType")

                    goodsholder_id = None
                    substituted_ilpn = ""

                    if event in ("GOODSHOLDER_MEASURED", "PUTAWAY_TASK_COMPLETED", "ROUTING_TASK_COMPLETED"):
                        goodsholder_id = message_payload.get("data", {}).get("goodsholderId")
                    elif event == "PPK_DEI_TaskRelease":
                        task_data = message_payload.get("TaskData", {})
                        data_content = task_data.get("data")
                        if isinstance(data_content, list) and data_content:
                            task_details = data_content[0].get("TaskDetail", [])
                        elif isinstance(data_content, dict):
                            task_details = data_content.get("TaskDetail", [])
                        else:
                            task_details = []
                        if task_details and isinstance(task_details, list):
                            goodsholder_id = task_details[0].get("SourceContainerId")
                    elif event == "RETRIEVAL_TASK_COMPLETED":
                        data = message_payload.get("data", {})
                        completed = data.get("retrievalTaskCompleted", {})
                        goodsholder_id = completed.get("retrievedGoodsholderId")
                        substituted_ilpn = data.get("requestedGoodsholderId", "")
                    elif event == "PPK_DEI_PickingFeedback":
                        feedback = message_payload.get("feedback", [])
                        if feedback:
                            goodsholder_id = feedback[0].get("ContainerId")
                    elif event in ("PACK_TASK_FAILED", "REPLEN_TASK_COMPLETED"):
                        goodsholder_id = message_payload.get("data", {}).get("sourceGoodsholderId")
                    elif event == "PTW_DEI_AllocationCreated":
                        details = message_payload.get("PutawayTaskDetails", {}).get("TaskDetailDTOs", [])
                        if details:
                            goodsholder_id = details[0].get("SourceContainerId")
                    elif event == "PICK_TASK_COMPLETED":
                        goodsholder_id = message_payload.get("data", {}).get("goodsholderId")
                    elif event == "PackTaskResult":
                        goodsholder_id = message_payload.get("data", {}).get("outboundGoodsholderId")
                    elif event == "Pack_Complete":
                        goodsholder_id = message_payload.get("oLPNDetails", {}).get("OlpnId")
                    elif event == "GOODSHOLDER_DIVERTED_DUE_TO_EXCEPTION":
                        goodsholder_id = message_payload.get("data", {}).get("goodsholderId")

                    if not goodsholder_id:
                        continue

                    status = entry.get("Status")
                    if status in ("NO DESTINATION FOUND", "SPLIT CREATED"):
                        continue

                    rows.append(
                        {
                            "Envn": environment.upper(),
                            "Plant": plant_id,
                            "MessageID": entry.get("MessageId"),
                            "LPN_ID": goodsholder_id,
                            "Substitute_From_iLPN": substituted_ilpn,
                            "Message_Type": (
                                "EXECUTE_REPLEN_TASK"
                                if entry.get("MessageType") == "PTW_DEI_AllocationCreated"
                                else entry.get("MessageType")
                            ),
                            "Status": status,
                            "User": header_info.get("User"),
                            "Created_on": header_info.get("MessageTimeStamp"),
                        }
                    )

            except requests.exceptions.RequestException as exc:
                logging.error("API request failed for iLPN payload %s: %s", index, exc)
            except (json.JSONDecodeError, TypeError) as exc:
                logging.error("Failed to parse iLPN response payload %s: %s", index, exc)
            except Exception as exc:
                logging.error("Unexpected iLPN error for payload %s: %s", index, exc)

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows).sort_values(by=["LPN_ID", "Created_on"])

    def _collect_olpn_results(self, payloads: list, environment: str, plant_id: str) -> pd.DataFrame:
        api_url, headers = self._get_api_context(environment, plant_id)
        rows = []

        for index, payload in enumerate(payloads, start=1):
            try:
                logging.info("[oLPN] Processing payload %s/%s", index, len(payloads))
                response = requests.post(url=api_url, headers=headers, json=payload)
                response.raise_for_status()
                results = response.json().get("data", {}).get("Results", [])

                for entry in results:
                    header_info = entry.get("headers", {})
                    message_payload_str = entry.get("Stage1", {}).get("MessagePayload", "{}")
                    message_payload = json.loads(message_payload_str)
                    event = message_payload.get("event", {}).get("type") or message_payload.get("MessageType")

                    goodsholder_id = None
                    if event in ("GOODSHOLDER_MEASURED", "ROUTING_TASK_COMPLETED"):
                        goodsholder_id = message_payload.get("data", {}).get("goodsholderId")
                    elif event == "PPK_DEI_TaskRelease":
                        task_data = message_payload.get("TaskData", {})
                        data_content = task_data.get("data")
                        if isinstance(data_content, list) and data_content:
                            task_details = data_content[0].get("TaskDetail", [])
                        elif isinstance(data_content, dict):
                            task_details = data_content.get("TaskDetail", [])
                        else:
                            task_details = []
                        if task_details and isinstance(task_details, list):
                            goodsholder_id = task_details[0].get("OlpnId")
                    elif event == "PACK_TASK_FAILED":
                        goodsholder_id = message_payload.get("data", {}).get("sourceGoodsholderId")
                    elif event == "PICK_TASK_COMPLETED":
                        goodsholder_id = message_payload.get("data", {}).get("goodsholderId")
                    elif event == "PackTaskResult":
                        goodsholder_id = message_payload.get("data", {}).get("outboundGoodsholderId")
                    elif event == "Pack_Complete":
                        goodsholder_id = message_payload.get("oLPNDetails", {}).get("OlpnId")
                    elif event == "GOODSHOLDER_DIVERTED_DUE_TO_EXCEPTION":
                        goodsholder_id = message_payload.get("data", {}).get("goodsholderId")

                    if not goodsholder_id:
                        continue

                    status = entry.get("Status")
                    if status in ("NO DESTINATION FOUND", "SPLIT CREATED"):
                        continue

                    spur_id = ""
                    if event == "ROUTING_TASK_COMPLETED":
                        spur_id = (
                            message_payload.get("data", {})
                            .get("routingTaskCompleted", {})
                            .get("routedToDestinationLocationId", "")
                        )

                    rows.append(
                        {
                            "Envn": environment.upper(),
                            "Plant": plant_id,
                            "MessageID": entry.get("MessageId"),
                            "LPN_ID": goodsholder_id,
                            "Spur_ID": spur_id,
                            "Message_Type": entry.get("MessageType"),
                            "Status": status,
                            "User": header_info.get("User"),
                            "Created_on": header_info.get("MessageTimeStamp"),
                        }
                    )

            except requests.exceptions.RequestException as exc:
                logging.error("API request failed for oLPN payload %s: %s", index, exc)
            except (json.JSONDecodeError, TypeError) as exc:
                logging.error("Failed to parse oLPN response payload %s: %s", index, exc)
            except Exception as exc:
                logging.error("Unexpected oLPN error for payload %s: %s", index, exc)

        if not rows:
            return pd.DataFrame()

        return pd.DataFrame(rows).sort_values(by=["LPN_ID", "Created_on"])

    @staticmethod
    def _to_excel_bytes(ilpn_df: pd.DataFrame, olpn_df: pd.DataFrame) -> bytes:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            if ilpn_df.empty:
                pd.DataFrame([{"Info": "No iLPN results found"}]).to_excel(
                    writer, sheet_name="iLPN", index=False
                )
            else:
                ilpn_df.to_excel(writer, sheet_name="iLPN", index=False)

            if olpn_df.empty:
                pd.DataFrame([{"Info": "No oLPN results found"}]).to_excel(
                    writer, sheet_name="oLPN", index=False
                )
            else:
                olpn_df.to_excel(writer, sheet_name="oLPN", index=False)

        return buffer.getvalue()

    def run_for_wave(self, wave_number: str, environment: str, plant_id: str) -> dict:
        ilpn_payloads, olpn_payloads = self._build_wave_payloads(
            wave_number=wave_number,
            environment=environment,
            plant_id=plant_id,
        )

        ilpn_df = self._collect_ilpn_results(ilpn_payloads, environment, plant_id)
        olpn_df = self._collect_olpn_results(olpn_payloads, environment, plant_id)
        excel_bytes = self._to_excel_bytes(ilpn_df, olpn_df)

        return {
            "ilpn_df": ilpn_df,
            "olpn_df": olpn_df,
            "excel_bytes": excel_bytes,
            "excel_name": f"MHE_Journal_Outbound_{wave_number}.xlsx",
            "ilpn_payload_count": len(ilpn_payloads),
            "olpn_payload_count": len(olpn_payloads),
        }

