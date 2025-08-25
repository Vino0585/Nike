import logging
import pandas as pd
from pathlib import Path

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 1. Get the path to the directory containing this script.
SCRIPT_DIR = Path(__file__).resolve().parent
# 2. Define the project root relative to this script.
PROJECT_ROOT = SCRIPT_DIR.parent
# 3. Construct the full, robust path to the Excel file.
DEFAULT_EXCEL_PATH = PROJECT_ROOT / 'Input_files/Worksheet.xlsx'
MASTER_EXCEL_PATH = PROJECT_ROOT / 'Input_files/Worksheet.xlsx'


class Worksheet:
    def __init__(self, excel_path=DEFAULT_EXCEL_PATH, master_path=MASTER_EXCEL_PATH):
        self.excel_file_path = excel_path
        self.master_file_path = master_path
        self.list_of_entry = []
        self.all_asn_create_parameters = []
        self.all_asn_search_parameters = []
        self.all_goods_holder_announced_parameters = []
        self.all_goods_holder_weighed_parameters = []
        self.all_putaway_complete_parameters = []
        self.all_inbound_delivery_extract_param = []
        self.all_verify_asn_extract_param = []
        self.all_master_sheet_extract_param = []
        self.all_msg_type_parameters = []
        self.all_lpn_parameter = []

    def _excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            # The hardcoded path is now gone! It uses the one from __init__.
            if not Path(self.excel_file_path).is_file():
                logging.error(f"Error: The file '{self.excel_file_path}' was not found.")

            # self.excel_file_path = "J30/Input_files/Worksheet.xlsx"
            xls = pd.ExcelFile(self.excel_file_path)
            sheet_names = xls.sheet_names
            logging.info(f"Sheets found in '{self.excel_file_path}': {sheet_names}")
            if input_sheet_name not in sheet_names:
                logging.error(f"Sheet {input_sheet_name} not found in the Excel file.")
            df = pd.read_excel(self.excel_file_path,
                               sheet_name=input_sheet_name,
                               dtype=str)  # This is where you have to feed the program name in the future.
            # print(f"\nData from {input_sheet_name} sheet:")
            # print(df)

            if not df.empty:
                data_dict_index = df.to_dict(orient='index')
                for key, value in data_dict_index.items():
                    self.list_of_entry.append(value)
            else:
                raise ValueError("Sheet 'CreateASN' is empty or no data found in the first row.")

        except FileNotFoundError:
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")
            return False
        except ValueError as ve:
            logging.error(f"Data error during Excel reading: {ve}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading Excel: {e}")
            return False
        return True

    def _master_excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            # The hardcoded path is now gone! It uses the one from __init__.
            if not Path(self.master_file_path).is_file():
                logging.error(f"Error: The file '{self.master_file_path}' was not found.")

            # self.excel_file_path = "J30/Input_files/Worksheet.xlsx"
            xls = pd.ExcelFile(self.master_file_path)
            sheet_names = xls.sheet_names
            logging.info(f"Sheets found in '{self.master_file_path}': {sheet_names}")
            if input_sheet_name not in sheet_names:
                logging.error(f"Sheet {input_sheet_name} not found in the Excel file.")
            df = pd.read_excel(self.master_file_path,
                               sheet_name=input_sheet_name,
                               dtype=str)  # This is where you have to feed the program name in the future.
            # print(f"\nData from {input_sheet_name} sheet:")
            # print(df)

            if not df.empty:
                data_dict_index = df.to_dict(orient='index')
                for key, value in data_dict_index.items():
                    self.list_of_entry.append(value)
            else:
                logging.error("Sheet 'CreateASN' is empty or no data found in the first row.")

        except FileNotFoundError:
            logging.error(f"Error: The file '{self.master_file_path}' was not found.")
            return False
        except ValueError as ve:
            logging.error(f"Data error during Excel reading: {ve}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading Excel: {e}")
            return False
        return True


    def create_asn_extract_parameters(self):
        self.all_asn_create_parameters = []

        # Step 1 to open the excel sheet and store list of entry.
        if not self._excel_open(input_sheet_name='CreateASN'):
            logging.error(f"Error: The file '{self.excel_file_path}' was not found.")

        # We need a list to store the extracted parameters for each ASN,
        # as there will be multiple ASNs.
        # Let's say you want to store a list of dictionaries, each representing an ASN's parameters.
        if not self.list_of_entry:
            logging.error("No ASN entries found to extract parameters.")
            return None

        for i, entry_dict in enumerate(self.list_of_entry):
            # Extract parameters for the current row/entry
            plant = entry_dict.get("Plant")
            user_initial = entry_dict.get("Initial")
            num_of_asn = int(entry_dict.get('Number of ASN', 0))
            item = entry_dict.get("Item")
            qty = entry_dict.get('Qty')
            case_qty = entry_dict.get('Case qty')
            envn = entry_dict.get("Environment")
            o_facility = entry_dict.get("Origin Facility", '0005005401')
            carrier_id = entry_dict.get("CarrierId", 'AUPU')

            # Ensure case_qty is not zero to prevent division by zero errors later
            if case_qty == 0:  # Use the local 'case_qty'
                print(
                    f"Warning: 'Case qty' for Entry {i + 1} is zero in Excel, defaulting to 1 to avoid division by zero.")
                case_qty = 1

            # Store the extracted parameters, perhaps in a new dictionary
            # or directly use them for whatever processing comes next.
            asn_params = {
                "Plant": plant,
                "Initial": user_initial,
                "Number of ASN": num_of_asn,
                "Item": item,
                "Qty": qty,
                "Case qty": case_qty,
                "Environment": envn,
                "O_Facility": o_facility,
                "Carrier": carrier_id
            }
            self.all_asn_create_parameters.append(asn_params)  # Add to our new list

        return self.all_asn_create_parameters

    def search_item_extract_parameters(self):

        # Step 1: Open the excel sheet and store the list of entries.
        if not self._excel_open(input_sheet_name='ItemSearch'):
            logging.error(f"Error: The input sheet ItemSearch not found in the Excel file.")
            return []

        if not self.list_of_entry:
            logging.error("No ItemSearch entries found to extract parameters.")
            return []

        all_item_parameters = []
        validation_errors = []
        # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment"]

        # Enumerate to get the index 'i' for helpful error messages.
        for i, entry in enumerate(self.list_of_entry):
            # The Excel row number is the list index + 2 (1 for 0-based index, 1 for the header row).
            excel_row_num = i + 2

            # Find all missing fields for the current entry
            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                # If any required fields are missing, record an error for this row.
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue  # Skip to the next entry

            # If the entry is valid, extract its parameters.
            params = {
                "plant": entry.get("Plant"),
                "environment": entry.get("Environment"),
                "num_of_items_to_search": entry.get("Num_of_Items_to_search"),
                "search_by_item": entry.get("Search_by_Item"),
                "search_by_product_type": entry.get("Search_by_Product_Type"),
                "search_by_missing_dims": entry.get("Search_by_Missing_Dims")
            }
            all_item_parameters.append(params)

        # After checking all entries, if we found any errors, print them all.
        if validation_errors:
            logging.error("Errors found in 'ItemSearch' sheet. Please correct them:")
            for error in validation_errors:
                logging.error(f"{error}")
            return []  # Return an empty list to indicate failure

        logging.info("All ItemSearch entries validated successfully.")
        return all_item_parameters

    def search_asn_extract_parameters(self):

        if not self._master_excel_open(input_sheet_name='SearchASN'):
            # The open method already logging.infos the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.info("No ItemSearch entries found to extract parameters.")
            return []

        # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            # The Excel row number is the list index + 2 (1 for 0-based index, 1 for the header row).
            excel_row_num = i + 1

            # Find all missing fields for the current entry
            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                # If any required fields are missing, record an error for this row.
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue  # Skip to the next entry

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")

            asn_search_params = {
                "Plant": plant,
                "Environment": envn,
                "ASNID": asn_id
            }
            self.all_asn_search_parameters.append(asn_search_params)  # Add to our new list

        return self.all_asn_search_parameters

    def goods_holder_announced(self):

        if not self._master_excel_open(input_sheet_name='MasterInput'):
            # The open method already prints the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.error("No ItemSearch entries found to extract parameters.")
            return []

            # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID", "LPNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")
            lpn_id = entry.get("LPNID")

            goods_holder_announced_params = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id,
                "LPN_ID": lpn_id
            }
            self.all_goods_holder_announced_parameters.append(goods_holder_announced_params)

        return self.all_goods_holder_announced_parameters

    def goods_holder_weighed(self):

        if not self._master_excel_open(input_sheet_name='MasterInput'):
            # The open method already prints the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.error("No ItemSearch entries found to extract parameters.")
            return []

            # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID", "LPNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")
            lpn_id = entry.get("LPNID")

            goods_holder_weighed_params = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id,
                "LPN_ID": lpn_id
            }
            self.all_goods_holder_weighed_parameters.append(goods_holder_weighed_params)

        return self.all_goods_holder_weighed_parameters

    def putaway_task_complete(self):

        if not self._master_excel_open(input_sheet_name='MasterInput'):
            # The open method already prints the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.error("No Putaway entries found to extract parameters.")
            return []

            # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID", "LPNID"]  # , "Failed"
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")
            lpn_id = entry.get("LPNID")
            failed = entry.get("Failed")
            cancelled = entry.get("Cancelled")

            putaway_complete_params = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id,
                "LPN_ID": lpn_id,
                "Failed": failed,
                "Cancelled": cancelled
            }
            self.all_putaway_complete_parameters.append(putaway_complete_params)

        return self.all_putaway_complete_parameters

    def inbound_delivery_worksheet_extract(self):

        if not self._master_excel_open(input_sheet_name='MasterInput'):
            # The open method already prints the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.error("No ASN for Inbound Delivery entries found to extract parameters.")
            return []

            # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")
            pre_allocate = entry.get("Pre_Allocate")

            inbound_delivery_extract_param = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id,
                "Pre_Allocate": pre_allocate
            }
            self.all_inbound_delivery_extract_param.append(inbound_delivery_extract_param)

        return self.all_inbound_delivery_extract_param

    def verify_asn_worksheet_extract(self):
        if not self._master_excel_open(input_sheet_name='MasterInput'):
            # The open method already prints the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.error("No ASN for ASN Verify entries found to extract parameters.")
            return []

            # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")

            verify_asn_extract_param = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id
            }
            self.all_verify_asn_extract_param.append(verify_asn_extract_param)

        return self.all_verify_asn_extract_param

    def extract_master_sheet_from_worksheet(self):
        if not self._excel_open(input_sheet_name='InboundMaster'):
            logging.error("No Master worksheet found to extract parameters.")
            return None

        if not self.list_of_entry:
            logging.error("No Inbound Master entries found to extract parameters.")
            return None

        required_field = ['CreateASN', 'RunAll']

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1
            missing_fields = [field for field in required_field if not entry.get(field)]
            if missing_fields:
                logging.error(f"Row {excel_row_num}: Validation failed. Required field(s) are empty: "
                              f"{', '.join(missing_fields)}")
                continue

            create_asn = entry.get("CreateASN")
            inbound_delivery = entry.get("InboundDelivery", 'N')
            preallocate = entry.get("PreAllocate", 'N')
            goods_holder_announced = entry.get("GHAnnounced", 'N')
            goods_holder_weighed = entry.get("GHWeighed", 'N')
            putaway_complete = entry.get("PutawayComplete", 'N')
            run_all = entry.get("RunAll")

            master_sheet_param = {
                "CreateASN": create_asn,
                "InboundDelivery": inbound_delivery,
                "PreAllocate": preallocate,
                "GH_Announced": goods_holder_announced,
                "GH_Weighed": goods_holder_weighed,
                "PutawayComplete": putaway_complete,
                "RunAll": run_all
            }
            self.all_master_sheet_extract_param.append(master_sheet_param)

        return self.all_master_sheet_extract_param

    def extract_mhe_journal_info(self):
        if not self._master_excel_open(input_sheet_name='MasterInput'):
            logging.error("No Master worksheet found to extract parameters.")
            return None

        if not self.list_of_entry:
            logging.error("No Inbound Master entries found to extract parameters.")
            return None

        required_fields = ["Plant", "Environment", "ASNID", "LPNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")
            lpn_id = entry.get("LPNID")

            goods_holder_weighed_params = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id,
                "LPN_ID": lpn_id
            }
            self.all_msg_type_parameters.append(goods_holder_weighed_params)

        return self.all_msg_type_parameters

    def extract_lpn_list(self):
        if not self._master_excel_open(input_sheet_name='MasterInput'):
            # The open method already prints the error, so we just exit.
            return []

        if not self.list_of_entry:
            logging.error("No ASN for LPN List entries found to extract parameters.")
            return []

            # Define which columns are mandatory for each row.
        required_fields = ["Plant", "Environment", "ASNID"]
        validation_errors = []

        for i, entry in enumerate(self.list_of_entry):
            excel_row_num = i + 1

            missing_fields = [field for field in required_fields if not entry.get(field)]

            if missing_fields:
                error_message = (f"Row {excel_row_num}: Validation failed. "
                                 f"Required field(s) are empty: {', '.join(missing_fields)}")
                validation_errors.append(error_message)
                continue

            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id = entry.get("ASNID")
            lpn_id = entry.get("LPNID")

            lpn_list_extract_param = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_id,
                "LPN_ID": lpn_id
            }
            self.all_lpn_parameter.append(lpn_list_extract_param)

        return self.all_lpn_parameter

# Work = Worksheet()
# payload = Work.extract_lpn_list()
# print(payload)
# Work = Worksheet()
# # # payload = Work.create_asn_extract_parameters()
# # # print(payload)
# # payload = Work.search_item_extract_parameters()
# # print(payload)
# payload = Work.search_asn_extract_parameters()
# print(payload)
# # payload = Work.inbound_delivery_worksheet_extract()
# # print(payload)
# # payload = Work.goods_holder_weighed()
# # print(payload)
# # payload = Work.putaway_task_complete()
# # print(payload)
# # payload = Work.verify_asn_worksheet_extract()
# # print(payload)
# payload = Work.extract_mhe_journal_info()
# print(payload)
# payload = Work.extract_master_sheet_from_worksheet()
# print(payload)


# self.plant = None
# self.num_of_asn = 0
# self.item = None
# self.qty = 0
# self.case_qty = 1
# self.o_facility = None
# self.asn_ids = []
# self.all_asn_payloads = []
# self.envn = ''
