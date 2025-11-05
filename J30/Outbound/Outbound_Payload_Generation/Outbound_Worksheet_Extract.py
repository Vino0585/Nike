import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = (SCRIPT_DIR.parent).parent
# 3. Construct the full, robust path to the Excel file.
DEFAULT_EXCEL_PATH = PROJECT_ROOT / 'Input_files/Outbound_Worksheet.xlsx'


class Outbound_Worksheet:
    def __init__(self, excel_path=DEFAULT_EXCEL_PATH):
        self.excel_file_path = excel_path
        # self.master_file_path = master_path
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

            df = ''
            if input_sheet_name == 'CreateOrder':
                df = pd.read_excel(self.excel_file_path, sheet_name=input_sheet_name, skiprows=1, dtype={'D_Facility': str})
            else:
                df = pd.read_excel(self.excel_file_path, sheet_name=input_sheet_name, dtype={'D_Facility': str})
            if not df.empty:
                data_dict_index = df.to_dict(orient='index')
                for key, value in data_dict_index.items():
                    self.list_of_entry.append(value)
            else:
                raise ValueError(f"Sheet {sheet_names} is empty or no data found in the first row.")

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


    def create_new_shipment_extract_parameter(self):
        self.all_create_shipment_parameters = []
        if not self._excel_open(input_sheet_name='CreateShipment'):
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False

        if not self.list_of_entry:
            logging.error("No Create Shipment entries found to extract parameters.")
            return False

        for i, entry_dict in enumerate(self.list_of_entry):
            # Extract parameters for the each row/entry
            plant = entry_dict.get("Plant")
            envn = entry_dict.get("Environment")
            create_shipment = entry_dict.get("Create_Shipment")
            carrier = entry_dict.get("Carrier")
            service_level = entry_dict.get("ServiceLevel")
            mode = entry_dict.get('Mode')


            create_shipment_params = {
                "plant": plant,
                "environment": envn,
                "create_shipment": create_shipment,
                "carrier": carrier,
                "service_level": service_level,
                "mode": mode,
            }
            self.all_create_shipment_parameters.append(create_shipment_params)  # Add to our new list

        return self.all_create_shipment_parameters

    def add_order_to_shipment_extract_parameter(self):
        self.all_add_order_to_shipment_parameters = []
        if not self._excel_open(input_sheet_name='OriginalOrderInput'):
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False

        add_order_extract = {}
        original_order_entry = self.list_of_entry
        order_ids = []
        for entry in original_order_entry:
            order_ids.append(entry.get('OrderID'))

        if not self._excel_open(input_sheet_name='Shipment_ID'):
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False

        shipment_id_info = self.list_of_entry

        plant = original_order_entry[0]["Plant"]
        environment = original_order_entry[0]["Environment"]
        shipment_id = shipment_id_info[0]["ShipmentId"]
        carrier_id = shipment_id_info[0]["Carrier"]
        mode = shipment_id_info[0]["Mode"]
        service_level = shipment_id_info[0]["Service_Level"]
        order_ids = order_ids

        add_order_extract = {
            'Plant': plant,
            'Environment': environment,
            'Shipment_ID': shipment_id,
            'Carrier_ID': carrier_id,
            'Order_ID': order_ids,
            'Mode': mode,
            'Service_Level': service_level
        }

        self.all_add_order_to_shipment_parameters.append(add_order_extract)
        return self.all_add_order_to_shipment_parameters

    def search_parent_order(self):
        self.all_search_order = []
        if not self._excel_open(input_sheet_name='OriginalOrderInput'):
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False

        original_order_entry = self.list_of_entry
        order_ids = []
        for entry in original_order_entry:
            order_ids.append(entry.get('OrderID'))

        plant = original_order_entry[0]["Plant"]
        environment = original_order_entry[0]["Environment"]

        search_order = {
            'Plant': plant,
            'Environment': environment,
            'Order_IDs': order_ids
        }

        self.all_search_order.append(search_order)
        return self.all_search_order


if __name__ == '__main__':
    Work = Outbound_Worksheet()
    # payload = Work.create_order_extract_parameters()
    # print(payload)
    # create_shipment = Work.create_new_shipment_extract_parameter()
    # print(create_shipment)
    # add_order_to_shipment = Work.add_order_to_shipment_extract_parameter()
    # print(add_order_to_shipment)
    # search_parent_order = Work.search_parent_order()
    # print(search_parent_order)
