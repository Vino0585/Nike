import logging
import pandas as pd
from pathlib import Path

from git.index.fun import entry_key

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Path to get the worksheet.
# 1. Get the path to the directory containing this script.
SCRIPT_DIR = Path(__file__).resolve().parent
# 2. Define the project root relative to this script.
PROJECT_ROOT = SCRIPT_DIR.parent.parent
# 3. Construct the full, robust path to the excel file.
inventory_excel_path = PROJECT_ROOT / 'Input_files/Inventory_WorkSheet.xlsx'


class Inventory_WorkSheet_Extract:
    def __init__(self, excel_path=inventory_excel_path):
        self.inventory_excel_file_path = excel_path
        self.all_search_iLPN_parameters = []
        self.list_of_entry = []

    def _excel_open(self, input_sheet_name):
        self.list_of_entry = []
        try:
            if not Path(self.inventory_excel_file_path).is_file():
                logging.error(f"Error: '{self.inventory_excel_file_path}' was not found.")

            xls = pd.ExcelFile(self.inventory_excel_file_path)
            sheet_names = xls.sheet_names
            logging.info(f"Sheets found in '{self.inventory_excel_file_path}' are: {sheet_names}")
            if input_sheet_name not in sheet_names:
                logging.error(f"Sheet {input_sheet_name} not found in the Excel file.")
            df = pd.read_excel(self.inventory_excel_file_path, sheet_name=input_sheet_name,
                               dtype=str)

            if not df.empty:
                data_dict_index = df.to_dict(orient='index')
                for key, value in data_dict_index.items():
                    self.list_of_entry.append(value)
            else:
                logging.error(f"Sheet '{input_sheet_name}' was not found in the Excel file.")

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

    def search_iLPN_parameters(self):
        self.all_search_iLPN_parameters = []

        if not self._excel_open(input_sheet_name='iLPN_Info'):
            logging.error(f"Error: The sheet name in '{self.inventory_excel_file_path}' was not found.")


        if not self.list_of_entry:
            logging.error(f"No iLPN entry found to extract parameters from {self.list_of_entry}.")
            return None

        for i, entry_dict in enumerate(self.list_of_entry):
            # Extracting parameter from excel sheet iLPN_Info
            plant = entry_dict.get("Plant")
            envn = entry_dict.get("Environment")
            asn_ids = entry_dict.get("ASN_ID(S)", 0)
            asn_flag = entry_dict.get("ASN_FLAG", 'N')
            ilpns_ids = entry_dict.get("iLPN_ID(S)", 0)
            lpn_flag = entry_dict.get("LPN_FLAG", 'N')
            condition_codes = entry_dict.get("ConditionCodes", 'N')
            condition_code_flag = entry_dict.get("Condition_Code_Flag", 'N')
            diversion_codes = entry_dict.get("Diversion_Codes", "N")
            diversion_code_flag = entry_dict.get("Diversion_Code_Flag", 'N')
            item_ids = entry_dict.get("ITEM_IDS", 0)
            status = entry_dict.get("Status", "Not Allocated")
            location = entry_dict.get("Location", 0)
            location_flag = entry_dict.get("Location_Flag", 'N')

            lpn_params = {
                "Plant": plant,
                "Environment": envn,
                "ASN_ID": asn_ids,
                "ASN_FLAG": asn_flag,
                "iLPN_ID": ilpns_ids,
                "LPN_FLAG": lpn_flag,
                "ConditionCodes": condition_codes,
                "Condition_Code_Flag": condition_code_flag,
                "Diversion_Codes": diversion_codes,
                "Diversion_Code_Flag": diversion_code_flag,
                "ITEM_IDS": item_ids,
                "STATUS": status,
                "Location": location,
                "Location_Flag": location_flag
            }
            self.all_search_iLPN_parameters.append(lpn_params)

        return self.all_search_iLPN_parameters

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
                "search_by_missing_dims": entry.get("Search_by_Missing_Dims"),
                "search_by_style": entry.get("Search_by_Style")
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

if __name__ == "__main__":
    invn = Inventory_WorkSheet_Extract()
    print(invn.search_iLPN_parameters())
    print(invn.search_item_extract_parameters())