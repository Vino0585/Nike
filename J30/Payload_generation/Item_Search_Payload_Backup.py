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
            def create_package(query):
                return {
                    "envn": params.get("environment"),
                    "plant": params.get("plant"),
                    "payload": query
                }

            query_string = {}

            # --- Condition 1: Search by specific Item IDs ---
            if pd.notna(item_ids_string) and str(item_ids_string).strip():
                item_id_list = str(item_ids_string).split(';')
                quoted_item_ids = ",".join([f"'{item.strip()}'" for item in item_id_list if item.strip()])
                query_string = {
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

            # --- Condition 2: Search by specific Item IDs that has no dims---
            elif pd.notna(item_no_dims):
                # --- Condition 2.1: Search by specific Item IDs that has no dims but with specific product type---
                if pd.notna(product_type):
                    product_code = PRODUCT_CODE_MAP.get(product_type)
                    query_string = {
                                "ViewName": "Item",
                                "Filters": [
                                    {
                                        "ViewName": "Item", "AttributeId": "Extended.DivisionCode", "Operator": "=",
                                        "FilterValues": [product_code]
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Extended.MarkForCubiscan",
                                        "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Length",
                                        "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Width",
                                        "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Height",
                                        "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Volume",
                                        "Operator": "=", "FilterValues": "NULL"
                                    },
                                ],
                                "SortOrder": "asc", "SortIndicator": "chevron-up", "TimeZone": "Japan",
                                "ComponentName": "com-manh-cp-item-master", "MaxCountLimit": size,
                                "Size": size, "Sort": "ItemId"
                            }
                # --- Condition 2.2: Search by specific Item IDs that has no dims but without specific product type---
                else:
                    query_string = {
                                "ViewName": "Item",
                                "Filters": [
                                    {
                                        "ViewName": "Item", "AttributeId": "Extended.MarkForCubiscan", "Operator": "=",
                                        "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Length", "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Width", "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Height", "Operator": "=", "FilterValues": "NULL"
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Volume", "Operator": "=", "FilterValues": "NULL"
                                    },
                                ],
                                "SortOrder": "asc", "SortIndicator": "chevron-up", "TimeZone": "Japan",
                                "ComponentName": "com-manh-cp-item-master", "MaxCountLimit": size, "Size": size,
                                "Sort": "ItemId"
                            }

            # --- Condition 3: Search by specific product ids for the item search ---
            elif pd.notna(product_type):
                product_code = PRODUCT_CODE_MAP.get(product_type)
                if product_code is not None:
                    query_string = {
                                "ViewName": "Item",
                                "Filters": [
                                    {
                                        "ViewName": "Item", "AttributeId": "Extended.DivisionCode", "Operator": "=",
                                        "FilterValues": product_code
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Length", "Operator": "!=",
                                        "FilterValues": None
                                    },
                                    {
                                        "ViewName": "Item", "AttributeId": "Extended.MarkForCubiscan", "Operator": "!=",
                                        "FilterValues": None
                                    }
                                ],
                                "SortOrder": "asc", "SortIndicator": "chevron-up", "TimeZone": "Japan",
                                "ComponentName": "com-manh-cp-item-master", "Sort": "ItemId",
                                "Size": size,
                            }

            # --- Condition 4: Search by count of items needed ---
            elif pd.notna(num_of_items):
                query_string = {
                    "ViewName": "Item",
                    "Filters": [
                        {
                            "ViewName": "Item", "AttributeId": "Length", "Operator": "!=", "FilterValues": "NULL"
                        },
                        {
                            "ViewName": "Item", "AttributeId": "Width", "Operator": "!=", "FilterValues": "NULL"
                        },
                        {
                            "ViewName": "Item", "AttributeId": "Height", "Operator": "!=", "FilterValues": "NULL"
                        },
                        {
                            "ViewName": "Item", "AttributeId": "Volume", "Operator": "!=", "FilterValues": "NULL"
                        },
                    ],
                    "SortOrder": "asc", "SortIndicator": "chevron-up", "TimeZone": "Japan",
                    "ComponentName": "com-manh-cp-item-master", "MaxCountLimit": size, "Size": size,
                    "Sort": "ItemId"
                }

            # --- return the above conditions to the final payload. ---
            if query_string:
                all_payloads.append(create_package(query_string))

        return all_payloads

# To execute to debug
if __name__ == '__main__':
    py = ItemPayload()
    # Use pprint for more readable output of complex objects
    import pprint
    pprint.pprint(py.create_item_search_payloads())