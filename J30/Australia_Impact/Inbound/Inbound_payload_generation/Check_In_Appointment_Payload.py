import datetime
import logging
import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Australia_Impact.Inbound.Inbound_payload_generation.Worksheet_extract import Worksheet
from Australia_Impact.Inbound.Inbound_payload_generation.Inbound_State_Manager import StateManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Check_In_Appointment_Payload_Generator:
    def __init__(self):
        self.worksheet = Worksheet()
        self.state_manager = StateManager()
        self.all_check_in_payloads = []

    def _next_trailer_id(self) -> str:
        trailer_prefix = datetime.datetime.now().strftime("T%m%d%y")
        trailer_sequence = self.state_manager.increment_counter(
            counter_name="trailer_nbr",
            start=1,
            min_value=1,
            max_value=99,
            scope=trailer_prefix,
        )
        trailer_id = f"{trailer_prefix}{trailer_sequence:02d}"
        return trailer_id

    @staticmethod
    def _schedule_time_default() -> str:
        return (datetime.datetime.now() + datetime.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")

    @property
    def generate_payloads(self) -> list:
        worksheet_rows = self.worksheet.check_in_appointment_worksheet_extract()
        if not worksheet_rows:
            logging.warning("No valid check-in rows found in MasterInput.")
            return []

        self.all_check_in_payloads = []

        for row in worksheet_rows:
            plant_id = str(row.get("Plant", "")).strip()
            environment = str(row.get("Environment", "")).strip()
            inbound_deliveries = row.get("InboundDeliveries", [])
            appointment_ids = row.get("AppointmentIds", [])
            appointment_type_id = str(row.get("AppointmentTypeId", "DROP_UNLOAD")).strip() or "DROP_UNLOAD"
            visit_type = str(row.get("VisitType", "DROP_UNLOAD")).strip() or "DROP_UNLOAD"
            carrier_id = str(row.get("CarrierId", "AUPU")).strip() or "AUPU"
            trailer_id = str(row.get("TrailerId", "")).strip() or self._next_trailer_id()
            equipment_type_id = (
                str(row.get("EquipmentTypeId", "40 FT CONTAINER (69 cube)")).strip()
                or "40 FT CONTAINER (69 cube)"
            )
            location_id = str(row.get("LocationId", "8001")).strip() or "8001"
            appointment_schedule_time = (
                str(row.get("AppointmentScheduleTime", "")).strip() or self._schedule_time_default()
            )

            if not (plant_id and environment and inbound_deliveries and appointment_ids):
                continue

            trailer_contents = [{"InboundShipment": shipment_id} for shipment_id in inbound_deliveries]

            for appointment_id in appointment_ids:
                payload = {
                    "AppointmentInfo": {
                        "AppointmentId": appointment_id,
                        "AppointmentScheduleTime": appointment_schedule_time,
                        "AppointmentTypeId": appointment_type_id,
                    },
                    "TrailerInfo": {
                        "CarrierId": carrier_id,
                        "TrailerId": trailer_id,
                        "EquipmentTypeId": equipment_type_id,
                    },
                    "VisitType": visit_type,
                    "YardId": plant_id,
                    "LocationId": location_id,
                    "FacilityId": plant_id,
                    "TrailerContents": trailer_contents,
                }
                self.all_check_in_payloads.append(
                    {"payload": payload, "environment": environment, "plant": plant_id}
                )

        logging.info(f"Generated {len(self.all_check_in_payloads)} check-in payload(s).")
        return self.all_check_in_payloads


if __name__ == "__main__":
    generator = Check_In_Appointment_Payload_Generator()
    payloads = generator.generate_payloads
    if payloads:
        import json

        for idx, payload in enumerate(payloads, start=1):
            logging.info(f"\n--- Check-In Appointment Payload {idx} ---")
            print(json.dumps(payload, indent=2))
