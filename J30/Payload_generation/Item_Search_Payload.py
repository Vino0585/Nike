import random

from Payload_generation.Worksheet_extract import Worksheet
import pandas as pd

class ItemPayload():
    def __init__(self):
        self.worksheet = Worksheet()

    def create_item_search_payloads(self) -> list:
        """
        Reads item search parameters from the worksheet and creates a list of API payloads.
        Handles multiple rows and multiple items per row (separated by ';').
        """
        all_item_parameters = self.worksheet.search_item_extract_parameters()

        if not all_item_parameters:
            print("No valid item parameters found, cannot create any payloads.")
            return []

        all_payloads = []
        template_structure = {
            "ItemId": None, "WeightUomId": None, "Weight": None, "VolumeUomId": None,
            "Volume": None, "Height": None, "Length": None, "Width": None, "PrimaryBarCode": None,
            "DimensionUomId": None, "CriticalDimension1": None,
            "CriticalDimension2": None, "CriticalDimension3": None, "ProductClass": None,
            "Extended": {"MarkForCubiscan": None, "DivisionCode": None}
        }

        PRODUCT_CODE_MAP = {
            'Apparel': 10,
            'Footwear': 20,
            'Equipment': 30
        }

        for params in all_item_parameters:
            item_ids_string = params.get("search_by_item")
            num_of_items = params.get("num_of_items_to_search")
            item_no_dims = params.get("search_by_missing_dims")
            product_type = params.get("search_by_product_type")
            size = 0

            # Helper function to create the final packaged payload
            def create_package(query_string, size, page):

                internal_page = page
                if internal_page != None:
                    internal_page = random.randint(1, 5)

                payload = {
                    "Query": query_string,
                    "Template": template_structure,
                    "Size": size,
                    "Page": internal_page,
                    "MaxCountLimit": size,
                    "EnableMaxCountLimit": True,
                }
                return {
                    "envn": params.get("environment"),
                    "plant": params.get("plant"),
                    "payload": payload
                }

            # --- Priority 1: Search by specific Item IDs ---
            if pd.notna(item_ids_string) and str(item_ids_string).strip():
                item_id_list = str(item_ids_string).split(';')
                size = len(item_id_list)
                page = None
                for item in item_id_list:
                    item_id = item.strip()
                    if not item_id:
                        continue

                    # Consistently create the full package for every payload
                    query = f"ItemId = '{item_id}'"
                    all_payloads.append(create_package(query, size, page))
                continue

            # --- Priority 2: Search by other criteria ---
            query_string = None


            if pd.notna(item_no_dims) and pd.notna(num_of_items):
                if pd.notna(product_type):
                    product_code = PRODUCT_CODE_MAP.get(product_type)
                    query_string = (f"Extended.DivisionCode = {product_code} AND Extended.MarkForCubiscan = NULL AND "
                                    f"Length = NULL AND Width = NULL AND Height = NULL AND Volume = NULL")
                    size = int(num_of_items)
                else:
                    query_string = (f"Extended.MarkForCubiscan = NULL AND Length = NULL AND Width = NULL AND "
                                    f"Height = NULL AND Volume = NULL")
                    size = int(num_of_items)


            elif pd.notna(product_type) and pd.notna(num_of_items):
                product_code = PRODUCT_CODE_MAP.get(product_type)
                if product_code is not None:
                    query_string = (f"Extended.DivisionCode = {product_code} AND Length != NULL AND "
                                    f"Extended.MarkForCubiscan != NULL")
                    size = int(num_of_items)

            elif pd.notna(num_of_items):
                size = int(num_of_items)
                query_string = (f"Length != NULL AND Width != NULL AND Height != NULL AND Volume != NULL")


            # If any of the criteria above created a query, build the payload
            if query_string:
                all_payloads.append(create_package(query_string, size))

        return all_payloads

# To execute to debug
if __name__ == '__main__':
    py = ItemPayload()
    # Use pprint for more readable output of complex objects
    import pprint

    pprint.pprint(py.create_item_search_payloads())