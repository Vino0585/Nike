import logging
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Dock_Door_Check_Payload_Generator:
    def __init__(self):
        self.worksheet = Worksheet()
        self.all_payloads = []

    @staticmethod
    def _build_payload(time_zone: str, size: int, max_count_limit: int) -> dict:
        return {
            "ViewName": "DockDoor",
            "Filters": [
                {
                    "ViewName": "DockDoor",
                    "AttributeId": "DockDoorStatusId",
                    "DataType": None,
                    "requiredFilter": False,
                    "Operator": "=",
                    "FilterValues": ["AVAILABLE"],
                    "negativeFilter": False,
                },
            ],
            "RequestAttributeIds": [],
            "SearchOptions": [],
            "SearchChains": [],
            "FilterExpression": None,
            "Page": 0,
            "TotalCount": -1,
            "SortOrder": "asc",
            "MultiSort": [],
            "SortIndicator": "chevron-up",
            "TimeZone": time_zone or "Australia/Melbourne",
            "IsCommonUI": False,
            "ComponentShortName": None,
            "EnableMaxCountLimit": True,
            "MaxCountLimit": max_count_limit,
            "PageQuery": None,
            "ChildQuery": None,
            "ComponentName": "com-manh-cp-dcinventory",
            "Size": size,
            "AdvancedFilter": False,
            "Sort": "DockDoorId",
        }

    @property
    def generate_payloads(self) -> list:
        rows = self.worksheet.dock_door_check_worksheet_extract()
        if not rows:
            logging.warning("No valid rows found for dock door check payload generation.")
            return []

        self.all_payloads = []
        for row in rows:
            plant = row.get("Plant")
            environment = row.get("Environment")
            time_zone = row.get("TimeZone", "Australia/Melbourne")
            size = int(row.get("Size", 25))
            max_count_limit = int(row.get("MaxCountLimit", 500))

            payload = self._build_payload(time_zone=time_zone, size=size, max_count_limit=max_count_limit)
            self.all_payloads.append(
                {"payload": payload, "plant": str(plant), "environment": str(environment)}
            )

        logging.info(f"Generated {len(self.all_payloads)} dock door check payload(s).")
        return self.all_payloads


if __name__ == "__main__":
    generator = Dock_Door_Check_Payload_Generator()
    payloads = generator.generate_payloads
    if payloads:
        import json

        for i, item in enumerate(payloads, start=1):
            logging.info(f"\n--- Dock Door Check Payload {i} ---")
            print(json.dumps(item, indent=2))
