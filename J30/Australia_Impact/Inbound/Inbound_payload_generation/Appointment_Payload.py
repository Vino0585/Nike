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


class Appointment_Payload_Generator:
    @staticmethod
    def _normalize_qty(value, default_qty=12) -> int:
        try:
            if value is None or str(value).strip() == "":
                return default_qty
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return default_qty

    def __init__(self):
        self.worksheet = Worksheet()
        self.state_manager = StateManager()
        self.all_appointment_payloads = []

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
    def _created_timestamp_now() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    @staticmethod
    def _preferred_window_start_plus_5_days() -> str:
        return (datetime.datetime.now() + datetime.timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _window_end_plus_6_days() -> str:
        return (datetime.datetime.now() + datetime.timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _build_shipment_association(shipment_id: str, shipped_qty: int) -> dict:
        return {
            "ShipmentId": shipment_id,
            "MaxStatus": "In Transit",
            "CreatedTimestamp": Appointment_Payload_Generator._created_timestamp_now(),
            "MinStatus": "In Transit",
            "ReceivedQty": 0,
            "Extended": {},
            "ShippedQty": shipped_qty,
            "Priority": 1,
        }

    @staticmethod
    def _build_appointment_contents(shipment_id: str) -> dict:
        return {"InboundShipment": shipment_id}

    @staticmethod
    def _build_shipment_stop(shipment_id: str, shipped_qty: int) -> dict:
        return {
            "ShipmentId": shipment_id,
            "ShipmentStopDetails": [{"Conveyable": False, "Uom": "lpn", "Quantity": shipped_qty}],
        }

    @property
    def generate_payloads(self) -> list:
        worksheet_rows = self.worksheet.appointment_worksheet_extract()
        if not worksheet_rows:
            logging.warning("No valid appointment rows found in MasterInput.")
            return []

        self.all_appointment_payloads = []

        for row_index, row in enumerate(worksheet_rows, start=2):
            plant_id = str(row.get("Plant", "")).strip()
            environment = str(row.get("Environment", "")).strip()
            inbound_deliveries = row.get("InboundDeliveries", [])
            inbound_delivery_qty_map = row.get("InboundDeliveryQtyMap", {})
            carrier_id = str(row.get("CarrierId", "AUPU")).strip() or "AUPU"
            comments = str(row.get("Comments", "VGTesting")).strip() or "VGTesting"
            equipment_type_id = str(row.get("EquipmentTypeId", "40 FT CONTAINER (69 cube)")).strip() or "40 FT CONTAINER (69 cube)"
            appointment_type_id = str(row.get("AppointmentTypeId", "DROP_UNLOAD")).strip() or "DROP_UNLOAD"

            if not (plant_id and environment and inbound_deliveries):
                logging.error(f"Row {row_index}: Missing plant/environment/inbound deliveries for appointment payload.")
                continue

            shipment_association = []
            appointment_contents = []
            shipment_stops = []
            for shipment_id in inbound_deliveries:
                shipped_qty = self._normalize_qty(inbound_delivery_qty_map.get(shipment_id))
                shipment_association.append(self._build_shipment_association(shipment_id, shipped_qty))
                appointment_contents.append(self._build_appointment_contents(shipment_id))
                shipment_stops.append(self._build_shipment_stop(shipment_id, shipped_qty))

            preferred_datetime = self._preferred_window_start_plus_5_days()
            window_end_datetime = self._window_end_plus_6_days()

            payload = {
                "ContentType": "INBOUND_SHIPMENTS",
                "FacilityId": plant_id,
                "SupplierPoAppointment": False,
                "ShipmentAsnAssociation": shipment_association,
                "MultipleStopsAtFacility": False,
                "AppointmentContents": appointment_contents,
                "ShipmentStop": shipment_stops,
                "AppointmentId": None,
                "CarrierId": carrier_id,
                "AppointmentTypeId": appointment_type_id,
                "PreferredDateTime": preferred_datetime,
                "ArrivalDateTime": None,
                "WindowStartDateTime": preferred_datetime,
                "WindowEndDateTime": window_end_datetime,
                "EstimatedArrivalDateTime": None,
                "Duration": 90,
                "VendorId": "",
                "Comments": comments,
                "TrailerId": self._next_trailer_id(),
                "EquipmentTypeId": equipment_type_id,
                "DriverId": None,
                "UserLoadInformation": [],
                "Resources": [],
                "PlannedDockDoors": [],
            }

            self.all_appointment_payloads.append(
                {
                    "payload": payload,
                    "environment": environment,
                    "plant": plant_id,
                    "inbound_deliveries": inbound_deliveries,
                }
            )

        logging.info(f"Generated {len(self.all_appointment_payloads)} appointment payload(s).")
        return self.all_appointment_payloads


if __name__ == "__main__":
    generator = Appointment_Payload_Generator()
    payloads = generator.generate_payloads
    if payloads:
        import json

        for idx, payload in enumerate(payloads, start=1):
            logging.info(f"\n--- Appointment Payload {idx} ---")
            print(json.dumps(payload, indent=2))
