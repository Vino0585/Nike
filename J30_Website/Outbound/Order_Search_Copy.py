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
from Outbound.Outbound_Payload_Generation.Search_Order_Payload import Search_Order_Payload


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class OrderSearchCopy:
    """Streamlit-friendly copy of outbound order search processing."""

    SEARCH_MODES = {
        "original_order_search": {
            "program": "OriginalOrderSearch",
            "sheet_name": "Original_Order_Search",
            "empty_message": "No original order rows returned",
            "excel_prefix": "Original_Order_Search",
        },
        "parent_order_search": {
            "program": "ParentOrderSearch",
            "sheet_name": "Parent_Order_Search",
            "empty_message": "No parent order rows returned",
            "excel_prefix": "Parent_Order_Search",
        },
    }

    def __init__(self):
        self.payload_builder = Search_Order_Payload()

    @staticmethod
    def _normalize_mode(search_mode: str) -> str:
        normalized_mode = (search_mode or "parent_order_search").strip().lower().replace(" ", "_")
        if normalized_mode not in OrderSearchCopy.SEARCH_MODES:
            raise ValueError(f"Unsupported order search mode: {search_mode}")
        return normalized_mode

    def _build_payloads(
        self,
        order_ids: list[str],
        environment: str,
        plant_id: str,
        search_mode: str,
    ) -> list[dict]:
        normalized_ids = [str(order_id).strip() for order_id in order_ids if str(order_id).strip()]
        if not normalized_ids:
            return []

        normalized_mode = self._normalize_mode(search_mode)
        query_values = "','".join(normalized_ids)
        query_field = "OriginalOrderId" if normalized_mode == "original_order_search" else "OrderLine.OriginalOrderId"
        return [
            {
                "Plant": plant_id,
                "Environment": environment,
                "Payload": {
                    "Query": f"{query_field} in ('{query_values}')",
                },
            }
        ]

    @classmethod
    def _get_api_context(cls, environment: str, plant_id: str, search_mode: str) -> tuple[str, dict]:
        normalized_mode = cls._normalize_mode(search_mode)
        token_handler = Get_Token(env=environment.lower(), plant=plant_id)
        bearer_token = token_handler.get_bearer()

        awm_env = AWM_OB_Env()
        awm_env.get_wm_host(host=environment.lower(), facility=plant_id)
        api_url = awm_env.get_program_url(program=cls.SEARCH_MODES[normalized_mode]["program"])

        headers = {
            "Content-Type": "application/json",
            "organization": str(plant_id),
            "location": str(plant_id),
            "Authorization": f"Bearer {bearer_token}",
        }
        return api_url, headers

    @staticmethod
    def _normalize_rows(extracted_data, environment: str, plant_id: str, search_mode: str) -> list[dict]:
        if not extracted_data:
            return []

        if isinstance(extracted_data, list):
            normalized_rows = []
            for row in extracted_data:
                if isinstance(row, dict):
                    row_copy = dict(row)
                    if search_mode == "original_order_search":
                        row_copy.setdefault("Plant", plant_id)
                        row_copy.setdefault("Environment", environment.upper())
                    normalized_rows.append(row_copy)
                else:
                    normalized_rows.append(
                        {
                            "Plant": plant_id if search_mode == "original_order_search" else None,
                            "Environment": environment.upper() if search_mode == "original_order_search" else None,
                            "OrderId": row,
                        }
                    )
            return normalized_rows

        return [
            {
                "Plant": plant_id,
                "Environment": environment.upper(),
                "OrderId": extracted_data,
            }
        ]

    @staticmethod
    def _parse_original_order_response_safe(response_data: dict, environment: str, plant_id: str) -> list[dict]:
        result = response_data.get("data") or []
        if not result:
            return []

        status_code = {
            "0500": "Draft",
            "1000": "Released",
            "2090": "Allocated",
            "7200": "Packed",
            "7800": "Loaded",
            "8000": "Shipped",
            "9000": "Cancelled",
        }

        original_order_data = []
        for order_data in result:
            order_status = status_code.get(str(order_data.get("MaximumStatus")), order_data.get("MaximumStatus"))
            order_data_extended = order_data.get("Extended") or {}
            order_data_order_line = order_data.get("OriginalOrderLine") or []

            for line in order_data_order_line:
                order_line_extended = line.get("Extended") or {}
                requested_services = line.get("OriginalOrderLineRequestedServices") or [None]

                for each_requested_service in requested_services:
                    service = each_requested_service or {}
                    row = {
                        "Plant": order_data.get("OrgId", plant_id),
                        "Environment": environment.upper(),
                        "OrderId": order_data.get("OriginalOrderId"),
                        "OrderType": order_data.get("OrderType"),
                        "Status": order_status,
                        "LoadingGroup": order_data_extended.get("LoadingGroup"),
                        "ShipTo": order_data.get("DestinationFacilityId"),
                        "Shipment": order_data.get("DesignatedShipmentId"),
                        "Carrier": order_data_extended.get("CarrierCode"),
                        "ServiceLvl": order_data_extended.get("ServiceLevelCode"),
                        "HUB": order_data_extended.get("CarrierHubCode"),
                        "SUB_HUB": order_data_extended.get("CarrierSubHubCode"),
                        "ItemName": line.get("ItemId"),
                        "Qty": line.get("OrderedQuantity"),
                        "FullPrice": order_line_extended.get("FullPrice"),
                        "DiscountPrice": order_line_extended.get("DiscountPrice"),
                        "GiftBag": order_data_extended.get("NikeGiftBagPrice"),
                        "ExternalGiftBagPrice": order_data_extended.get("ExternalGiftBagPrice"),
                        "ShippingCharge": order_data_extended.get("ShippingCharge"),
                        "Sequence": service.get("Sequence"),
                        "ServiceTypeID": service.get("ServiceTypeId"),
                        "ProvidedServiceId": service.get("ProvidedServiceId"),
                        "ServiceUomId": service.get("ServiceUomId"),
                        "PONumber": order_data_extended.get("ExternalPurchaseOrderNumber"),
                    }
                    original_order_data.append(row)

        return original_order_data

    def _get_parser(self, search_mode: str):
        normalized_mode = self._normalize_mode(search_mode)
        if normalized_mode == "original_order_search":
            return self._parse_original_order_response_safe
        return self.payload_builder.parse_parent_order_line_response

    def _collect_results(
        self,
        payloads: list[dict],
        environment: str,
        plant_id: str,
        search_mode: str,
    ) -> pd.DataFrame:
        if not payloads:
            return pd.DataFrame()

        normalized_mode = self._normalize_mode(search_mode)
        api_url, headers = self._get_api_context(environment, plant_id, normalized_mode)
        parser = self._get_parser(normalized_mode)
        rows = []

        for index, payload in enumerate(payloads, start=1):
            try:
                logging.info("[Order Search:%s] Processing payload %s/%s", normalized_mode, index, len(payloads))
                response = requests.post(
                    api_url,
                    json=payload.get("Payload", {}),
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                response_data = response.json()
                if normalized_mode == "original_order_search":
                    extracted_data = parser(response_data, environment, plant_id)
                else:
                    extracted_data = parser(response_data)
                rows.extend(self._normalize_rows(extracted_data, environment, plant_id, normalized_mode))
            except requests.exceptions.HTTPError as exc:
                logging.error("HTTP error during order search payload %s: %s", index, exc)
                if exc.response is not None:
                    logging.error("Response content: %s", exc.response.text)
            except requests.exceptions.RequestException as exc:
                logging.error("Request error during order search payload %s: %s", index, exc)
            except Exception as exc:
                logging.error("Unexpected order search error for payload %s: %s", index, exc)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        if normalized_mode == "original_order_search" and "OrderId" in df.columns:
            df = df.sort_values(by=["OrderId"], kind="stable")
        elif normalized_mode == "parent_order_search":
            sort_columns = [column for column in ["Original_Order_id", "OrderId", "WaveID"] if column in df.columns]
            if sort_columns:
                df = df.sort_values(by=sort_columns, kind="stable")
        return df.reset_index(drop=True)

    @classmethod
    def _to_excel_bytes(cls, df: pd.DataFrame, search_mode: str) -> bytes:
        normalized_mode = cls._normalize_mode(search_mode)
        mode_config = cls.SEARCH_MODES[normalized_mode]
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            if df.empty:
                pd.DataFrame([{"Info": mode_config["empty_message"]}]).to_excel(
                    writer, sheet_name=mode_config["sheet_name"], index=False
                )
            else:
                df.to_excel(writer, sheet_name=mode_config["sheet_name"], index=False)
        return buffer.getvalue()

    def run_for_orders(
        self,
        order_ids: list[str],
        environment: str,
        plant_id: str,
        search_mode: str = "parent_order_search",
    ) -> dict:
        normalized_mode = self._normalize_mode(search_mode)
        mode_config = self.SEARCH_MODES[normalized_mode]
        payloads = self._build_payloads(
            order_ids=order_ids,
            environment=environment,
            plant_id=plant_id,
            search_mode=normalized_mode,
        )
        result_df = self._collect_results(
            payloads=payloads,
            environment=environment,
            plant_id=plant_id,
            search_mode=normalized_mode,
        )

        return {
            "df": result_df,
            "excel_bytes": self._to_excel_bytes(result_df, normalized_mode),
            "excel_name": f"{mode_config['excel_prefix']}_{len(order_ids)}_orders.xlsx",
            "request_count": len(payloads),
            "input_count": len(order_ids),
            "search_mode": normalized_mode,
        }

