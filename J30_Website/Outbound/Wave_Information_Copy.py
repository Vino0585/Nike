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
from Environment.WM_Outbound_API_EndPoint import AWM_OB_Env


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class WaveInformationCopy:
    """Streamlit-friendly copy of outbound wave information processing."""

    @staticmethod
    def _build_payload(wave_numbers: list[str]) -> dict:
        normalized_waves = [str(wave).strip() for wave in wave_numbers if str(wave).strip()]
        quoted_waves = "','".join(normalized_waves)
        return {
            "Query": f"OrderPlanningRunId in ('{quoted_waves}')"
        }

    @staticmethod
    def _get_api_context(environment: str, plant_id: str) -> tuple[str, dict]:
        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()

        awm_env = AWM_OB_Env()
        awm_env.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = awm_env.get_program_url(program="oLPNSearch")

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "organization": str(plant_id),
            "location": str(plant_id),
        }
        return api_url, headers

    @staticmethod
    def _parse_rows(response_data: dict) -> list[dict]:
        result = response_data.get("data") or []
        if not result:
            return []

        lpn_status = {
            "1000": "Created",
            "7000": "Picked",
            "7200": "Packed",
            "7800": "Loaded",
            "7900": "Pending ShipConfirmation",
            "8000": "Shipped",
        }

        rows = []
        for lpn in result:
            lpn_extended = lpn.get("Extended", {})
            lpn_details = lpn.get("OlpnDetail", []) or []
            for detail in lpn_details:
                rows.append(
                    {
                        "OlpnId": detail.get("OlpnId"),
                        "Created_by": lpn.get("CreatedBy"),
                        "Status": lpn_status.get(str(lpn.get("Status")), lpn.get("Status")),
                        "Item": detail.get("ItemId"),
                        "Qty": detail.get("InitialQuantity"),
                        "Tracking_nbr": lpn.get("TrackingNumber"),
                        "PickLocn": lpn.get("PickLocationId"),
                        "PSGroupDest": lpn_extended.get("PackStationGroupDestination"),
                        "Wave_nbr": lpn.get("OrderPlanningRunId"),
                        "Carrier": lpn.get("CarrierId"),
                        "OriginalOrderId": detail.get("OriginalOrderId"),
                        "AggregatedOrder": detail.get("OrderId"),
                        "LoadingGroup": lpn_extended.get("LoadingGroup"),
                        "oLPNType": lpn.get("ContainerTypeId")
                    }
                )
        return rows

    def _collect_results(self, wave_numbers: list[str], environment: str, plant_id: str) -> pd.DataFrame:
        if not wave_numbers:
            return pd.DataFrame()

        api_url, headers = self._get_api_context(environment, plant_id)
        payload = self._build_payload(wave_numbers)

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        rows = self._parse_rows(response.json())
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        sort_columns = [column for column in ["Wave_nbr", "OlpnId", "OriginalOrderId"] if column in df.columns]
        if sort_columns:
            df = df.sort_values(by=sort_columns, kind="stable")
        return df.reset_index(drop=True)

    @staticmethod
    def _to_excel_bytes(df: pd.DataFrame) -> bytes:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            if df.empty:
                pd.DataFrame([{"Info": "No wave rows returned"}]).to_excel(
                    writer, sheet_name="Wave_Information", index=False
                )
            else:
                df.to_excel(writer, sheet_name="Wave_Information", index=False)
        return buffer.getvalue()

    def run_for_waves(self, wave_numbers: list[str], environment: str, plant_id: str) -> dict:
        result_df = self._collect_results(
            wave_numbers=wave_numbers,
            environment=environment,
            plant_id=plant_id,
        )

        return {
            "df": result_df,
            "excel_bytes": self._to_excel_bytes(result_df),
            "excel_name": f"Wave_Information_{len(wave_numbers)}_waves.xlsx",
            "request_count": 1 if wave_numbers else 0,
            "input_count": len(wave_numbers),
        }

