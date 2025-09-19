import logging
import pandas as pd
from pathlib import Path

from Payload_generation.Worksheet_extract import MASTER_EXCEL_PATH

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
# 3. Construct the full, robust path to the Excel file.
DEFAULT_EXCEL_PATH = PROJECT_ROOT / 'Input_files/Outbound_Worksheet.xlsx'
MASTER_EXCEL_PATH = PROJECT_ROOT / 'Input_files/Outbound_Master_Sheet.xlsx'


class Outbound_Worksheet:
    def __init__(self, excel_path=DEFAULT_EXCEL_PATH, master_path=MASTER_EXCEL_PATH):
        self.excel_file_path = excel_path
        self.master_file_path = master_path
        self.list_of_entry = []
        self.all_order_create_parameters = []
        self.all_order_search_parameters = []


    def _excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            # The hardcoded path is now gone! It uses the one from __init__.
            if not Path(self.excel_file_path).is_file():
                logging.error(f"Error: The file '{self.excel_file_path}' was not found.")

            xls = pd.ExcelFile(self.excel_file_path)
            sheet_names = xls.sheet_names
            logging.info(f"Sheets found in '{self.excel_file_path}': {sheet_names}")
            if input_sheet_name not in sheet_names:
                logging.error(f"Sheet {input_sheet_name} not found in the Excel file.")
            df = pd.read_excel(self.excel_file_path, sheet_name=input_sheet_name, skiprows=1, dtype={'D_Facility': str})
            if not df.empty:
                data_dict_index = df.to_dict(orient='index')
                for key, value in data_dict_index.items():
                    self.list_of_entry.append(value)
            else:
                raise ValueError("Sheet 'CreateOrder' is empty or no data found in the first row.")

        except FileNotFoundError:
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False
        except ValueError as ve:
            logging.error(f"Error: {ve}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading Excel: {e}")
            return False
        return True

    def create_order_extract_parameters(self):
        self.all_order_create_parameters = []

        if not self._excel_open(input_sheet_name='CreateOrder'):
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False

        if not self.list_of_entry:
            logging.error("No Order entries found to extract parameters.")
            return False


        for i, entry_dict in enumerate(self.list_of_entry):
            # Extract parameters for the each row/entry
            plant = entry_dict.get("Plant")
            envn = entry_dict.get("Environment")
            user_initial = entry_dict.get("Initial")
            order_type = entry_dict.get("Order Type")
            num_of_order = int(entry_dict.get("Number of Orders", 0))
            item = entry_dict.get("Item(s)")
            qty = entry_dict.get('Quantity')
            d_facility = str(entry_dict.get("D_Facility", '0005005401'))
            pre_pack_code = entry_dict.get("PrePack Code")
            vas_code_service_id = entry_dict.get("VAS Code Service ID")
            vas_code_service_uom = entry_dict.get("VAS Code Service UOM")
            service_level = entry_dict.get("Service Level")
            address_1 = entry_dict.get("Address1")
            city = entry_dict.get("City")
            state = entry_dict.get("State")
            postal_code = entry_dict.get("Postal Code")
            first_name = entry_dict.get("First Name")
            email = entry_dict.get("Email")
            country = ''

            if plant == 1081:
                country = 'Japan'

            order_params = {
                "plant": plant,
                "environment": envn,
                "initial": user_initial,
                "number_of_Orders": num_of_order,
                "order_Type": order_type,
                "item": item,
                "qty": qty,
                "d_facility": d_facility,
                "pre_pack_Code": pre_pack_code,
                "vas_code_service_id": vas_code_service_id,
                "vas_code_service_uom": vas_code_service_uom,
                "service_level": service_level,
                "address_1": address_1,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "country": country,
                "first_name": first_name,
                "email": email,
                }
            self.all_order_create_parameters.append(order_params)  # Add to our new list

        return self.all_order_create_parameters
#
Work = Outbound_Worksheet()
payload = Work.create_order_extract_parameters()
print(payload)







