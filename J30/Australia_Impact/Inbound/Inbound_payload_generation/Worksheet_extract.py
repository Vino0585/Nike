import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCRIPT_DIR = Path(__file__).resolve().parent
AUSTRALIA_IMPACT_ROOT = SCRIPT_DIR.parent.parent
AU_INPUT_DIR = AUSTRALIA_IMPACT_ROOT / "Input_files"


def _resolve_default_excel_path() -> Path:
    return AU_INPUT_DIR / "Inbound_worksheet.xlsx"


class Worksheet:
    """
    Australia Impact worksheet reader.
    Reads only from Australia_Impact/Input_files.
    """

    def __init__(self, excel_path=None, master_path=None):
        self.excel_file_path = Path(excel_path) if excel_path else _resolve_default_excel_path()
        self.master_file_path = Path(master_path) if master_path else _resolve_default_excel_path()
        self.list_of_entry = []
        self.all_asn_create_parameters = []
        self.all_asn_search_parameters = []
        self.all_inbound_delivery_extract_param = []
        self.all_master_sheet_extract_param = []
        self.all_appointment_extract_param = []
        self.all_check_in_extract_param = []
        self.all_dock_door_check_param = []

    def _excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            if not self.excel_file_path.is_file():
                logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
                return False

            xls = pd.ExcelFile(self.excel_file_path)
            if input_sheet_name not in xls.sheet_names:
                logging.error(f"Sheet '{input_sheet_name}' not found in '{self.excel_file_path}'.")
                return False

            df = pd.read_excel(self.excel_file_path, sheet_name=input_sheet_name, dtype=str)
            if df.empty:
                logging.error(f"Sheet '{input_sheet_name}' is empty.")
                return False

            self.list_of_entry = list(df.fillna("").to_dict(orient="index").values())
            return True
        except Exception as ex:
            logging.error(f"Error reading '{input_sheet_name}' from '{self.excel_file_path}': {ex}")
            return False

    def _master_excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            if not self.master_file_path.is_file():
                logging.error(f"Error: The file '{self.master_file_path}' was not found.")
                return False

            xls = pd.ExcelFile(self.master_file_path)
            if input_sheet_name not in xls.sheet_names:
                logging.error(f"Sheet '{input_sheet_name}' not found in '{self.master_file_path}'.")
                return False

            df = pd.read_excel(self.master_file_path, sheet_name=input_sheet_name, dtype=str)
            if df.empty:
                logging.error(f"Sheet '{input_sheet_name}' is empty.")
                return False

            self.list_of_entry = list(df.fillna("").to_dict(orient="index").values())
            return True
        except Exception as ex:
            logging.error(f"Error reading '{input_sheet_name}' from '{self.master_file_path}': {ex}")
            return False

    def create_asn_extract_parameters(self):
        self.all_asn_create_parameters = []
        if not self._excel_open(input_sheet_name="CreateASN"):
            return []

        required_fields = ["Plant", "Environment", "Item", "Qty", "Case qty", "Number of ASN"]
        for i, entry in enumerate(self.list_of_entry):
            missing = [field for field in required_fields if not str(entry.get(field, "")).strip()]
            if missing:
                logging.error(f"Row {i + 2}: Missing required fields in CreateASN: {', '.join(missing)}")
                continue

            self.all_asn_create_parameters.append(
                {
                    "Plant": entry.get("Plant"),
                    "Initial": entry.get("Initial", "VG"),
                    "Number of ASN": int(entry.get("Number of ASN", 0) or 0),
                    "Item": entry.get("Item"),
                    "Qty": entry.get("Qty"),
                    "Case qty": entry.get("Case qty"),
                    "Environment": entry.get("Environment"),
                    "O_Facility": entry.get("Origin Facility", "0005005401"),
                    "Carrier": entry.get("CarrierId", "AUPU"),
                }
            )

        return self.all_asn_create_parameters

    def search_asn_extract_parameters(self):
        self.all_asn_search_parameters = []
        if not self._master_excel_open(input_sheet_name="SearchASN"):
            return []

        required_fields = ["Plant", "Environment", "ASNID"]
        for i, entry in enumerate(self.list_of_entry):
            missing = [field for field in required_fields if not str(entry.get(field, "")).strip()]
            if missing:
                logging.error(f"Row {i + 2}: Missing required fields in SearchASN: {', '.join(missing)}")
                continue

            self.all_asn_search_parameters.append(
                {
                    "Plant": entry.get("Plant"),
                    "Environment": entry.get("Environment"),
                    "ASNID": entry.get("ASNID"),
                }
            )

        return self.all_asn_search_parameters

    def inbound_delivery_worksheet_extract(self):
        self.all_inbound_delivery_extract_param = []
        if not self._master_excel_open(input_sheet_name="MasterInput"):
            return []

        required_fields = ["Plant", "Environment", "ASNID"]
        for i, entry in enumerate(self.list_of_entry):
            missing = [field for field in required_fields if not str(entry.get(field, "")).strip()]
            if missing:
                logging.error(f"Row {i + 2}: Missing required fields in MasterInput: {', '.join(missing)}")
                continue

            self.all_inbound_delivery_extract_param.append(
                {
                    "Plant": entry.get("Plant"),
                    "Environment": entry.get("Environment"),
                    "ASN_ID": entry.get("ASNID"),
                    "Pre_Allocate": entry.get("Pre_Allocate", ""),
                }
            )

        return self.all_inbound_delivery_extract_param

    def extract_master_sheet_from_worksheet(self):
        self.all_master_sheet_extract_param = []
        if not self._excel_open(input_sheet_name="InboundMaster"):
            return []

        for i, entry in enumerate(self.list_of_entry):
            create_asn = str(entry.get("CreateASN", "")).strip() or "N"
            inbound_delivery = str(entry.get("InboundDelivery", "")).strip() or "N"
            appointment = str(entry.get("Appointment", "")).strip() or "N"
            run_all = str(entry.get("RunAll", "")).strip() or "N"

            self.all_master_sheet_extract_param.append(
                {
                    "CreateASN": create_asn,
                    "InboundDelivery": inbound_delivery,
                    "Appointment": appointment,
                    "RunAll": run_all,
                }
            )

        return self.all_master_sheet_extract_param

    def appointment_worksheet_extract(self):
        self.all_appointment_extract_param = []
        if not self._master_excel_open(input_sheet_name="MasterInput"):
            return []

        required_fields = ["Plant", "Environment", "InboundDelivery"]
        for i, entry in enumerate(self.list_of_entry):
            missing = [field for field in required_fields if not str(entry.get(field, "")).strip()]
            if missing:
                logging.error(f"Row {i + 2}: Missing required fields in MasterInput: {', '.join(missing)}")
                continue

            inbound_deliveries = [
                shipment_id.strip()
                for shipment_id in str(entry.get("InboundDelivery", "")).split(";")
                if shipment_id.strip()
            ]
            if not inbound_deliveries:
                logging.error(f"Row {i + 2}: InboundDelivery has no usable ShipmentId values.")
                continue

            seen = set()
            unique_inbound_deliveries = []
            for shipment_id in inbound_deliveries:
                if shipment_id in seen:
                    continue
                seen.add(shipment_id)
                unique_inbound_deliveries.append(shipment_id)

            qty_values_raw = [
                qty.strip()
                for qty in str(entry.get("IB_Delivery_QTY", "")).split(";")
                if qty.strip()
            ]
            shipment_qty_map = {}
            for idx, shipment_id in enumerate(unique_inbound_deliveries):
                qty_value = "12"
                if idx < len(qty_values_raw):
                    qty_value = qty_values_raw[idx]
                shipment_qty_map[shipment_id] = qty_value

            self.all_appointment_extract_param.append(
                {
                    "Plant": entry.get("Plant"),
                    "Environment": entry.get("Environment"),
                    "InboundDeliveries": unique_inbound_deliveries,
                    "InboundDeliveryQtyMap": shipment_qty_map,
                    "CarrierId": entry.get("CarrierId", "AUPU"),
                    "Comments": entry.get("Comments", "VGTesting"),
                    "EquipmentTypeId": entry.get("EquipmentTypeId", "40 FT CONTAINER (69 cube)"),
                    "AppointmentTypeId": entry.get("AppointmentTypeId", "DROP_UNLOAD"),
                }
            )

        return self.all_appointment_extract_param

    def check_in_appointment_worksheet_extract(self):
        self.all_check_in_extract_param = []
        if not self._master_excel_open(input_sheet_name="MasterInput"):
            return []

        required_fields = ["Plant", "Environment", "InboundDelivery", "Appt_id"]
        for i, entry in enumerate(self.list_of_entry):
            missing = [field for field in required_fields if not str(entry.get(field, "")).strip()]
            if missing:
                logging.error(f"Row {i + 2}: Missing required fields in MasterInput: {', '.join(missing)}")
                continue

            inbound_deliveries = [
                shipment_id.strip()
                for shipment_id in str(entry.get("InboundDelivery", "")).split(";")
                if shipment_id.strip()
            ]
            appointment_ids = [
                appt_id.strip()
                for appt_id in str(entry.get("Appt_id", "")).split(";")
                if appt_id.strip()
            ]

            if not inbound_deliveries or not appointment_ids:
                logging.error(
                    f"Row {i + 2}: InboundDelivery and Appt_id must contain at least one value."
                )
                continue

            self.all_check_in_extract_param.append(
                {
                    "Plant": entry.get("Plant"),
                    "Environment": entry.get("Environment"),
                    "InboundDeliveries": inbound_deliveries,
                    "AppointmentIds": appointment_ids,
                    "AppointmentTypeId": entry.get("AppointmentTypeId", "DROP_UNLOAD"),
                    "VisitType": entry.get("VisitType", "DROP_UNLOAD"),
                    "CarrierId": entry.get("CarrierId", "AUPU"),
                    "TrailerId": entry.get("TrailerId", ""),
                    "EquipmentTypeId": entry.get("EquipmentTypeId", "40 FT CONTAINER (69 cube)"),
                    "LocationId": entry.get("LocationId", "8001"),
                    "AppointmentScheduleTime": entry.get("AppointmentScheduleTime", ""),
                }
            )

        return self.all_check_in_extract_param

    def dock_door_check_worksheet_extract(self):
        self.all_dock_door_check_param = []
        if not self._master_excel_open(input_sheet_name="MasterInput"):
            return []

        required_fields = ["Plant", "Environment"]
        seen_keys = set()

        for i, entry in enumerate(self.list_of_entry):
            missing = [field for field in required_fields if not str(entry.get(field, "")).strip()]
            if missing:
                logging.error(f"Row {i + 2}: Missing required fields in MasterInput: {', '.join(missing)}")
                continue

            plant = str(entry.get("Plant", "")).strip()
            environment = str(entry.get("Environment", "")).strip()
            key = (plant, environment)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            self.all_dock_door_check_param.append(
                {
                    "Plant": plant,
                    "Environment": environment,
                    "TimeZone": entry.get("TimeZone", "Australia/Melbourne"),
                    "Size": int(entry.get("DockDoorPageSize", 25) or 25),
                    "MaxCountLimit": int(entry.get("DockDoorMaxCountLimit", 500) or 500),
                }
            )

        return self.all_dock_door_check_param
