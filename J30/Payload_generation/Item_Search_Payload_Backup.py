import random
import logging

from pandas.core.common import not_none

from Payload_generation.Worksheet_extract import Worksheet
import pandas as pd

# Setting up logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ItemPayload():
    def __init__(self):
        self.worksheet = Worksheet()

    def create_item_search_payloads(self) -> list:

        # 1. Getting Worksheet information.
        all_item_parameters = self.worksheet.search_item_extract_parameters()

        if not all_item_parameters:
            print("No valid item parameters found, cannot create any payloads.")
            return []


        # 2. Setting default parameters
        all_payloads = []
        size = 0

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
            item_style = params.get("search_by_style")
            item_color = params.get("search_by_color")
            style = ''
            color = ''

            if item_style:
                style = str(item_style).split(';')
            elif item_color:
                color = str(item_color).split(';')
            else:
                style = None
                color = None

            if num_of_items:
                size = int(num_of_items)
            elif style and color:
                if len(style) != len(color):
                    logging.info("The length of Style and Color mismatching therefore could not continue")
                    return []
                size = len(style)
            elif style:
                size = len(style)
            elif color:
                size = len(color)
            else:
                size = 1


            # Helper function to create the final packaged payload
            def create_package(query_string):
                payload = ''
                return {
                    "envn": params.get("environment"),
                    "plant": params.get("plant"),
                    "payload": payload
                }

            # --- Priority 1: Search by specific Item IDs ---
            if pd.notna(item_ids_string) and str(item_ids_string).strip():
                item_id_list = str(item_ids_string).split(';')
                quoted_item_ids = ",".join([f"'{item.strip()}'" for item in item_id_list if item.strip()])
                query = {
                            "ViewName": "Item",
                            "Filters": [
                                {
                                    "ViewName": "Item", "AttributeId": "ItemId", "Operator": "=",
                                    "FilterValues": [quoted_item_ids]
                                }
                            ],
                            "SortOrder": "asc", "SortIndicator": "chevron-up", "TimeZone": "Japan",
                            "ComponentName": "com-manh-cp-item-master", "Sort": "ItemId",
                            "Size": size,
                        }

                all_payloads.append(create_package(query))
                continue


            # --- Priority 2: Search by other criteria ---

            query_string = None
            if pd.notna(item_no_dims):
                if pd.notna(product_type):
                    product_code = PRODUCT_CODE_MAP.get(product_type)

                    query_string = {
                                        "ViewName": "Item",
                                        "Filters": [
                                            {
                                                "ViewName": "Item", "AttributeId": "Extended.DivisionCode", "Operator": "=",
                                                "FilterValues": [product_code]
                                            }
                                        ],
                                        "SortOrder": "asc", "SortIndicator": "chevron-up", "TimeZone": "Japan",
                                        "ComponentName": "com-manh-cp-item-master", "MaxCountLimit": size,
                                        "Size": 1,
                                        "Sort": "ItemId"
                                    }

                    query_string = (f"Extended.DivisionCode = {product_code} AND Extended.MarkForCubiscan = NULL AND "
                                    f"Length = NULL AND Width = NULL AND Height = NULL AND Volume = NULL")
                else:
                    query_string = (f"Extended.MarkForCubiscan = NULL AND Length = NULL AND Width = NULL AND "
                                    f"Height = NULL AND Volume = NULL")

            elif pd.notna(product_type):
                product_code = PRODUCT_CODE_MAP.get(product_type)
                if product_code is not None:
                    query_string = (f"Extended.DivisionCode = {product_code} AND Length != NULL AND "
                                    f"Extended.MarkForCubiscan != NULL")

            elif pd.notna(num_of_items):
                # FIX: Convert object to a query string. "is not null" is a common way to check for existence.
                query_string = (f"Length != NULL AND Width != NULL AND Height != NULL AND Volume != NULL")


            # If any of the criteria above created a query, build the payload
            if query_string:
                all_payloads.append(create_package(query_string))

        return all_payloads

# To execute to debug
if __name__ == '__main__':
    py = ItemPayload()
    # Use pprint for more readable output of complex objects
    import pprint

    pprint.pprint(py.create_item_search_payloads())