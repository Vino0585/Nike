import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR)

SCRIPT_DIR = Path(__file__).resolve().parent
AUSTRALIA_IMPACT_ROOT = SCRIPT_DIR.parent.parent  # .../Australia_Impact
DEFAULT_EXCEL_PATH = AUSTRALIA_IMPACT_ROOT / "Input_files" / "Outbound_Worksheet.xlsx"


class Outbound_Worksheet:
    def __init__(self, excel_path=None):
        self.excel_file_path = Path(excel_path) if excel_path else DEFAULT_EXCEL_PATH
        self.list_of_entry = []
        self.all_fr_order_create_parameters = []

    def _excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            if not self.excel_file_path.is_file():
                logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
                return False

            xls = pd.ExcelFile(self.excel_file_path)
            if input_sheet_name not in xls.sheet_names:
                logging.error(f"Sheet {input_sheet_name} not found in the Excel file.")
                return False

            if input_sheet_name == "Parent_Order":
                df = pd.read_excel(self.excel_file_path, sheet_name=input_sheet_name, skiprows=1)
            else:
                df = pd.read_excel(
                    self.excel_file_path,
                    sheet_name=input_sheet_name,
                    dtype={"D_Facility": str, "Sold_Facility": str, "Phone": str, "OrderIDs": str},
                )

            if df.empty:
                logging.error(f"Sheet '{input_sheet_name}' is empty.")
                return False

            data_dict_index = df.to_dict(orient="index")
            for _, value in data_dict_index.items():
                self.list_of_entry.append(value)
        except Exception as exc:
            logging.error(f"An unexpected error occurred while reading Excel: {exc}")
            return False
        return True

    def create_fr_order_extract_parameters(self):
        self.all_fr_order_create_parameters = []
        if not self._excel_open(input_sheet_name="Parent_Order"):
            return False

        if not self.list_of_entry:
            logging.error("No Order entries found to extract parameters.")
            return False

        for entry_dict in self.list_of_entry:
            plant = entry_dict.get("Plant")
            envn = entry_dict.get("Environment")
            user_initial = entry_dict.get("Initial")
            order_type = entry_dict.get("Order Type")
            num_of_order = int(entry_dict.get("Number of Orders", 0))
            item = entry_dict.get("Item(s)")
            gtin = f"00{entry_dict.get('GTIN')}"
            qty = entry_dict.get("Quantity")
            ship_to = str(entry_dict.get("Ship_Facility"))
            d_facility = str(ship_to).zfill(10) if ship_to is not None else ""
            pre_pack_code = entry_dict.get("PrePack Code")
            instruction_code = entry_dict.get("Instruction_Code")
            instruction_text = entry_dict.get("Instruction_Text")
            service_level = entry_dict.get("Service Level")
            address_1 = entry_dict.get("Address1")
            city = entry_dict.get("City")
            state = str(entry_dict.get("State")).zfill(2)
            postal_code = entry_dict.get("Postal Code")
            first_name = entry_dict.get("First Name", "null")
            email = entry_dict.get("B2CField Email", entry_dict.get("Email", "null"))
            phone_raw = entry_dict.get("Phone")
            phone = "" if (phone_raw is None or pd.isna(phone_raw)) else str(phone_raw)
            address_2 = entry_dict.get("Address2")
            street_address1 = entry_dict.get("StreetAddress1")
            street_address2 = entry_dict.get("StreetAddress2")
            carrier_code = entry_dict.get("CarrierCode")
            hub_code = entry_dict.get("HUBCode")
            sub_hub = entry_dict.get("SUBHUB")
            route_number = entry_dict.get("Route_nbr")
            mark_for_customer_id = entry_dict.get("Mark_for")
            sold_to_facility_id_raw = entry_dict.get("Sold_Facility")
            pickup_dttm = str(entry_dict.get("PickupDTTM"))
            delivery_dttm = str(entry_dict.get("DeliveryDTTM"))
            dlvd = entry_dict.get("DLVD")
            sold_to_facility_id = str(sold_to_facility_id_raw).zfill(10) if sold_to_facility_id_raw is not None else ""
            country = entry_dict.get("CountryCode")
            if country is None or (isinstance(country, float) and pd.isna(country)):
                country = "JP" if plant == 1081 else ""

            self.all_fr_order_create_parameters.append(
                {
                    "plant": plant,
                    "environment": envn,
                    "initial": user_initial,
                    "number_of_Orders": num_of_order,
                    "order_Type": order_type,
                    "item": item,
                    "qty": qty,
                    "d_facility": d_facility,
                    "pre_pack_Code": pre_pack_code,
                    "instruction_code": instruction_code,
                    "instruction_text": instruction_text,
                    "service_level": service_level,
                    "address_1": address_1,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                    "country": country,
                    "first_name": first_name,
                    "email": email,
                    "phone": phone,
                    "carrier_code": carrier_code,
                    "hub_code": hub_code,
                    "route_number": route_number,
                    "mark_for_customer_id": mark_for_customer_id,
                    "sold_to_facility_id": sold_to_facility_id,
                    "sub_hub": sub_hub,
                    "pickup_dttm": pickup_dttm,
                    "delivery_dttm": delivery_dttm,
                    "dlvd": dlvd,
                    "gtin": gtin,
                    "address_2": address_2,
                    "street_address1": street_address1,
                    "street_address2": street_address2,
                    # Optional AU-specific overrides (minimal-safe model with defaults in payload builder).
                    "language_code": entry_dict.get("LanguageCode"),
                    "currency_code": entry_dict.get("CurrencyCode"),
                    "sales_organization_code": entry_dict.get("SalesOrganizationCode"),
                    "sales_delivery_priority": entry_dict.get("SalesDeliveryPriority"),
                    "appointment_scheduling_indicator": entry_dict.get("AppointmentSchedulingIndicator"),
                    "division_code": entry_dict.get("DivisionCode"),
                    "material_group_code": entry_dict.get("MaterialGroupCode"),
                    "customer_account_type": entry_dict.get("CustomerAccountType"),
                    "channel_class_code": entry_dict.get("ChannelClassCode"),
                    "sales_unit_uom": entry_dict.get("SalesUnitQuantityUOM"),
                    "base_unit_uom": entry_dict.get("BaseUnitQuantityUOM"),
                    "net_price_amount": entry_dict.get("NetPriceAmount"),
                    "msrp_amount": entry_dict.get("ManufacturersSuggestedRetailPrice"),
                    "gross_weight": entry_dict.get("GrossWeight"),
                    "net_weight": entry_dict.get("NetWeight"),
                    "weight_uom": entry_dict.get("WeightUOM"),
                }
            )

        return self.all_fr_order_create_parameters
