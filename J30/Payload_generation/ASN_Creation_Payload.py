from Payload_generation.Worksheet_extract import Worksheet
from Payload_generation.Number_Generation import NumberGeneration


class Asn_Payload_Generator:
    def __init__(self):
        """Initializes the generator."""
        self.worksheet = Worksheet()
        self.number_gen = NumberGeneration()
        self.all_asn_payloads = []

    def _parse_lpn_definitions_from_row(self, data_row: dict, row_num_in_sheet: int) -> list:
        """Parses item/qty strings from a row and returns a list of valid LPN definitions."""
        items_groups_str = str(data_row.get("Item", "")).split(';')
        qtys_groups_str = str(data_row.get('Qty', "")).split(';')
        case_qtys_groups_str = str(data_row.get('Case qty', "")).split(';')

        if not (len(items_groups_str) == len(qtys_groups_str) == len(case_qtys_groups_str)):
            print(f"--> WARNING: Mismatch in ';'-separated groups in row {row_num_in_sheet}. Skipping.")
            return []

        lpn_definitions = []
        for item_group, qty_group, case_qty_group in zip(items_groups_str, qtys_groups_str, case_qtys_groups_str):
            try:
                items = [item.strip() for item in item_group.split('@') if item.strip()]
                if not items:
                    continue

                qtys = [int(qty.strip()) for qty in qty_group.split('@') if qty.strip()]
                case_qtys = [int(cq.strip()) for cq in case_qty_group.split('@') if cq.strip()]

                if not (len(items) == len(qtys) == len(case_qtys)):
                    print(
                        f"--> WARNING: Mismatch in '@'-separated values for group '{item_group}' in row {row_num_in_sheet}. Skipping group.")
                    continue

                num_lpns_to_generate = qtys[0] // case_qtys[0] if case_qtys and case_qtys[0] > 0 else 0
                is_mixed = len(items) > 1

                if is_mixed:
                    for j in range(1, len(items)):
                        if case_qtys[j] == 0 or (qtys[j] // case_qtys[j]) != num_lpns_to_generate:
                            print(
                                f"--> ERROR: Inconsistent Qty/CaseQty ratio for mixed LPN group '{item_group}' in row {row_num_in_sheet}. Skipping group.")
                            num_lpns_to_generate = 0
                            break

                if num_lpns_to_generate > 0:
                    lpn_definitions.append({
                        "is_mixed": is_mixed, "items": items, "case_qtys": case_qtys,
                        "num_lpns_to_generate": num_lpns_to_generate
                    })
            except (ValueError, ZeroDivisionError) as e:
                print(f"--> ERROR: Invalid data in row {row_num_in_sheet} for group '{item_group}'. Details: {e}")
                continue

        return lpn_definitions

    def _build_lpn_list_for_asn(self, lpn_definitions: list, num_of_asn: int, asn_index: int, current_asn_id: str,
                                envn: str, plant: str) -> list:
        """Builds the list of LPN JSON objects for a single ASN."""
        lpn_list_for_current_asn = []
        for lpn_def in lpn_definitions:
            total_lpns_for_def = lpn_def['num_lpns_to_generate']
            lpns_in_this_asn = total_lpns_for_def // num_of_asn
            if asn_index < (total_lpns_for_def % num_of_asn):
                lpns_in_this_asn += 1

            if lpns_in_this_asn > 0:
                item_desc = "@".join(lpn_def['items'])
                lpn_type = "Mixed-Item" if lpn_def['is_mixed'] else "Single-Item"
                print(f"    - {lpn_type} Group '{item_desc}': Generating {lpns_in_this_asn} LPNs.")

            for _ in range(lpns_in_this_asn):
                current_lpn_id = self.number_gen.lpn_number_generation(envn)
                lpn_detail_list = [
                    {
                        "AsnId": current_asn_id, "ExpiryDate": "", "InventoryAttribute1": "01000",
                        "CountryOfOrigin": "CN", "ItemId": item_id, "ManufacturingDate": "",
                        "QuantityUomId": "LPN", "ShipByDate": "", "ShippedQuantity": case_qty,
                        "PurchaseOrderId": "25050501", "PurchaseOrderLineId": ""
                    } for item_id, case_qty in zip(lpn_def['items'], lpn_def['case_qtys'])
                ]
                lpn_extended = {"LpnHeight": "12", "LpnWidth": "12", "LpnLength": "24"}
                lpn_data = {
                    "AsnId": current_asn_id, "VendorId": None, "LpnId": current_lpn_id,
                    "LpnStatus": "1000", "OrgId": plant, "LpnSizeTypeId": 'CARTON',
                    "SingleItemLPN": "0" if lpn_def['is_mixed'] else "1",
                    "LpnTypeId": "ILPN", "Extended": lpn_extended, "LpnDetail": lpn_detail_list
                }
                lpn_list_for_current_asn.append(lpn_data)
        return lpn_list_for_current_asn

    @property
    def generate_payloads(self) -> list:
        """
        Get payload by reading the worksheet and processing each row.
        """
        try:
            list_of_datadict = self.worksheet.create_asn_extract_parameters()
            if list_of_datadict is None:
                print("Error: Worksheet method returned None. Halting generation.")
                return []
        except Exception as e:
            print(f"An unexpected error occurred while extracting data from the worksheet: {e}")
            return []

        if not list_of_datadict:
            print("No data rows found in the worksheet to process.")
            return []

        print(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

        # **CRITICAL FIX**: Reset the list before each run.
        # This ensures that calling `generate_payloads` twice doesn't accumulate results.
        self.all_asn_payloads = []

        for i, data_row in enumerate(list_of_datadict):
            # Excel rows are 1-based and have a header, so the first data row is at index 0, but is row 2 in the sheet.
            row_num_in_sheet = i + 2
            print(f"\n--- Processing Excel Row {row_num_in_sheet} ---")

            plant = data_row.get("Plant")
            num_of_asn = int(data_row.get('Number of ASN', 0))
            envn = data_row.get("Environment")
            o_facility = data_row.get("O_Facility", '0005005401')
            carrier_id = data_row.get("CarrierId", 'AUPU')

            lpn_definitions = self._parse_lpn_definitions_from_row(data_row, row_num_in_sheet)
            if not lpn_definitions:
                print(f"--> INFO: No valid LPNs to generate for row {row_num_in_sheet}. Skipping.")
                continue

            asn_ids = self.number_gen.asn_number_generation(num_of_asn, envn)
            if not asn_ids:
                print(f"--> INFO: Skipping row {row_num_in_sheet} as 'Number of ASN' is 0.")
                continue

            for asn_index, current_asn_id in enumerate(asn_ids):
                print(f"  ASN {current_asn_id}:")
                lpn_list = self._build_lpn_list_for_asn(lpn_definitions, num_of_asn, asn_index, current_asn_id, envn,
                                                        plant)

                if lpn_list:
                    bol, pro, trailer, seal = self.number_gen.misc_nbr(envn=envn)
                    asn_extended = {"BolNumber": bol, "ProNumber": pro, "SealNumber": seal}
                    asn_payload = {
                        "AsnId": current_asn_id, "AsnOriginTypeId": "P", "OriginFacilityId": o_facility,
                        "VendorId": None, "CarrierId": carrier_id, "BillOfLadingNumber": bol,
                        "ProNumber": pro, "OrgId": str(plant), "DestinationFacilityId": str(plant),
                        "AsnStatus": "1000", "AsnLevel": "LPN", "TrailerId": str(trailer), "Extended": asn_extended,
                        "Lpn": lpn_list
                    }
                    self.all_asn_payloads.append({'payload': asn_payload, 'environment': envn})

        print(f"\n--- Generation Complete. Total Payloads Created: {len(self.all_asn_payloads)} ---")
        return self.all_asn_payloads


# # This block is excellent for testing your class in isolation.
# if __name__ == "__main__":
#     asn_generator = Asn_Payload_Generator()
#     final_payloads = asn_generator.generate_payloads
#     # Optional: Pretty-print the first payload for verification
#     if final_payloads:
#         import json
#         for i, payloads in enumerate(final_payloads):
#             num = i+1
#             print(f"\n--- No {num} Generated Payload ---")
#             print(json.dumps(payloads, indent=2))



# Version 4
# from J30.Payload_generation.Worksheet_extract import Worksheet
# from J30.Payload_generation.Number_Generation import NumberGeneration
#
#
# # --- Main Class for ASN Payload Generation ---
# class Asn_Payload_Generator:
#     def __init__(self):
#         """Initializes the generator."""
#         self.worksheet = Worksheet()
#         # --- FIX: Create a SINGLE, shared instance of NumberGeneration ---
#         # This ensures that all counters increment correctly and are not reset.
#         self.number_gen = NumberGeneration()
#         self.all_generated_asn_ids = []
#         self.all_asn_payloads = []
#
#     def _generate_unique_asn_ids(self, num_of_asn_to_generate: int, envn: str) -> list:
#         """Generates a list of unique ASN IDs using the shared number generator."""
#         # Use the instance-level number generator
#         return self.number_gen.asn_number_generation(num_of_asn_to_generate, envn)
#
#     @property
#     def generate_payloads(self) -> list:
#         """
#         Orchestrates the entire process. It fetches data, parses single and mixed-item
#         definitions, validates them, generates the required ASNs and LPNs, and returns
#         a final list of all generated JSON payloads.
#         """
#         try:
#             list_of_datadict = self.worksheet.create_asn_extract_parameters()
#             if list_of_datadict is None:
#                 print("Error: Worksheet method returned None. Halting generation.")
#                 return []
#         except Exception as e:
#             print(f"An unexpected error occurred while extracting data from the worksheet: {e}")
#             return []
#
#         if not list_of_datadict:
#             print("No data rows found in the worksheet to process.")
#             return []
#
#         print(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")
#         # self.all_asn_payloads = []
#         # self.all_generated_asn_ids = []
#
#         for i, data_row in enumerate(list_of_datadict):
#             row_num_in_sheet = i + 1
#             print(f"\n--- Processing Excel Row {row_num_in_sheet} ---")
#
#             plant = data_row.get("Plant")
#             num_of_asn = int(data_row.get('Number of ASN', 0))
#             envn = data_row.get("Environment")
#             o_facility = str(data_row.get("O_Facility", '0005005401')) # Corrected key from your worksheet class
#
#             # --- Step 1: Parse LPN Groups (split by ';') ---
#             items_groups_str = str(data_row.get("Item", "")).split(';')
#             qtys_groups_str = str(data_row.get('Qty', "")).split(';')
#             case_qtys_groups_str = str(data_row.get('Case qty', "")).split(';')
#
#             if not (len(items_groups_str) == len(qtys_groups_str) == len(case_qtys_groups_str)):
#                 print(
#                     f"Warning: Mismatch in the number of ';'-separated groups in row {row_num_in_sheet}. Skipping this row.")
#                 continue
#
#             # --- Step 2: Process each LPN Group to create LPN definitions ---
#             lpn_definitions = []
#             is_row_valid = True
#             for item_group, qty_group, case_qty_group in zip(items_groups_str, qtys_groups_str, case_qtys_groups_str):
#                 items = [item.strip() for item in item_group.split('@') if item.strip()]
#
#                 if not items:
#                     continue
#
#                 try:
#                     qtys = [int(qty.strip()) for qty in qty_group.split('@') if qty.strip()]
#                     case_qtys = [int(cq.strip()) for cq in case_qty_group.split('@') if cq.strip()]
#                 except ValueError as e:
#                     print(
#                         f"Error: Invalid number in row {row_num_in_sheet}. Ensure all values are integers. Details: {e}")
#                     is_row_valid = False
#                     break
#
#                 if not (len(items) == len(qtys) == len(case_qtys)):
#                     print(
#                         f"Warning: Mismatch in '@'-separated values for group '{item_group}' in row {row_num_in_sheet}. Skipping this group.")
#                     continue
#
#                 # --- Calculate number of LPNs for this definition ---
#                 num_lpns_to_generate = 0
#                 if case_qtys and case_qtys[0] > 0:
#                     num_lpns_to_generate = qtys[0] // case_qtys[0]
#
#                 is_mixed = len(items) > 1
#                 if is_mixed:
#                     for j in range(1, len(items)):
#                         if case_qtys[j] == 0 or (qtys[j] // case_qtys[j]) != num_lpns_to_generate:
#                             print(
#                                 f"Error: Inconsistent Qty/CaseQty ratio for mixed LPN group '{item_group}' in row {row_num_in_sheet}. All items in a mixed group must result in the same number of LPNs. Skipping group.")
#                             num_lpns_to_generate = 0  # Invalidate this group
#                             break
#
#                 if num_lpns_to_generate > 0:
#                     lpn_definitions.append({
#                         "is_mixed": is_mixed,
#                         "items": items,
#                         "case_qtys": case_qtys,
#                         "num_lpns_to_generate": num_lpns_to_generate
#                     })
#
#             if not is_row_valid:
#                 continue
#
#             # --- Step 3: Generate ASN IDs for the current row ---
#             if not lpn_definitions:
#                 print(f"Warning: No valid LPN definitions found in row {row_num_in_sheet}. Skipping.")
#                 continue
#
#             asn_ids_for_this_row = self._generate_unique_asn_ids(num_of_asn, envn)
#             if not asn_ids_for_this_row:
#                 print(f"Skipping row {row_num_in_sheet} as no ASN IDs were generated (Number of ASN might be 0).")
#                 continue
#             self.all_generated_asn_ids.extend(asn_ids_for_this_row)
#
#             # --- Step 4: Distribute LPNs and build payloads ---
#             for asn_index, current_asn_id in enumerate(asn_ids_for_this_row):
#                 lpn_list_for_current_asn = []
#                 print(f"  ASN {current_asn_id}:")
#
#                 for lpn_def in lpn_definitions:
#                     total_lpns_for_def = lpn_def['num_lpns_to_generate']
#                     lpns_in_this_asn = total_lpns_for_def // num_of_asn
#                     if asn_index < (total_lpns_for_def % num_of_asn):
#                         lpns_in_this_asn += 1
#
#                     if lpns_in_this_asn > 0:
#                         item_desc = "@".join(lpn_def['items'])
#                         lpn_type = "Mixed-Item" if lpn_def['is_mixed'] else "Single-Item"
#                         print(f"    - {lpn_type} Group '{item_desc}': Generating {lpns_in_this_asn} LPNs.")
#
#                     for _ in range(lpns_in_this_asn):
#                         # --- FIX: Use the shared instance to get a unique LPN ID ---
#                         current_lpn_id = self.number_gen.lpn_number_generation(envn)
#
#                         lpn_detail_list = []
#                         for item_id, case_qty in zip(lpn_def['items'], lpn_def['case_qtys']):
#                             lpn_detail_list.append({
#                                 "AsnId": current_asn_id, "ExpiryDate": "", "InventoryAttribute1": "01000",
#                                 "CountryOfOrigin": "CN", "ItemId": item_id, "ManufacturingDate": "",
#                                 "QuantityUomId": "LPN", "ShipByDate": "", "ShippedQuantity": case_qty,
#                                 "PurchaseOrderId": "25050501", "PurchaseOrderLineId": ""
#                             })
#
#                         lpn_extended = {"LpnHeight": "12", "LpnWidth": "12", "LpnLength": "24", "LpnVendor": "0005005401"}
#                         lpn_data = {
#                             "AsnId": current_asn_id, "VendorId": None, "LpnId": current_lpn_id,
#                             "LpnStatus": "1000", "OrgId": plant,
#                             "SingleItemLPN": "0" if lpn_def['is_mixed'] else "1",
#                             "LpnTypeId": "ILPN", "Extended": lpn_extended, "LpnDetail": lpn_detail_list
#                         }
#                         lpn_list_for_current_asn.append(lpn_data)
#
#                 # --- FIX: Use the shared instance to get unique misc numbers ---
#                 bol, pro, trailer, seal = self.number_gen.misc_nbr(envn=envn)
#                 ASN_Extended = {"BolNumber": bol, "ProNumber": pro, "SealNumber": seal}
#
#                 if lpn_list_for_current_asn:
#                     asn_payload = {
#                         "AsnId": current_asn_id, "AsnOriginTypeId": "P", "OriginFacilityId": str(o_facility), "VendorId": None,
#                         "OrgId": str(plant), "DestinationFacilityId": str(plant),
#                         "AsnStatus": "1000", "AsnLevel": "LPN", "TrailerId": str(trailer), "Extended": ASN_Extended, "Lpn": lpn_list_for_current_asn
#                     }
#                     self.all_asn_payloads.append({'payload': asn_payload, 'environment': envn})
#
#         print(f"\n--- Generation Complete. Total Payloads Created: {len(self.all_asn_payloads)} ---")
#         return self.all_asn_payloads
#
#
# asn = Asn_Payload_Generator()
# payload = asn.generate_payloads
# print(payload)


# # Version 3

# from J30.Payload_generation.Worksheet_extract import Worksheet
# from J30.Payload_generation.Number_Generation import NumberGeneration
#
#
# # --- Main Class for ASN Payload Generation ---
# class Asn_Payload_Generator:
#     def __init__(self):
#         """Initializes the generator."""
#         self.worksheet = Worksheet()
#         self.all_generated_asn_ids = []
#         self.all_asn_payloads = []
#
#     def _generate_unique_asn_ids(self, num_of_asn_to_generate: int, envn: str) -> list:
#         """Generates a list of unique ASN IDs."""
#         asn_number = NumberGeneration()
#         return asn_number.asn_number_generation(num_of_asn_to_generate, envn)
#
#     @property
#     def generate_payloads(self) -> list:
#         """
#         Orchestrates the entire process. It fetches data, parses single and mixed-item
#         definitions, validates them, generates the required ASNs and LPNs, and returns
#         a final list of all generated JSON payloads.
#         """
#         try:
#             list_of_datadict = self.worksheet.create_asn_extract_parameters()
#             if list_of_datadict is None:
#                 print("Error: Worksheet method returned None. Halting generation.")
#                 return []
#         except Exception as e:
#             print(f"An unexpected error occurred while extracting data from the worksheet: {e}")
#             return []
#
#         if not list_of_datadict:
#             print("No data rows found in the worksheet to process.")
#             return []
#
#         print(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")
#         self.all_asn_payloads = []
#         self.all_generated_asn_ids = []
#
#         for i, data_row in enumerate(list_of_datadict):
#             row_num_in_sheet = i + 2
#             print(f"\n--- Processing Excel Row {row_num_in_sheet} ---")
#
#             plant = data_row.get("Plant")
#             num_of_asn = int(data_row.get('Number of ASN', 0))
#             envn = data_row.get("Environment")
#             o_facility = str(data_row.get("o_facility", '0005005401'))
#
#             # --- Step 1: Parse LPN Groups (split by ';') ---
#             items_groups_str = str(data_row.get("Item", "")).split(';')
#             qtys_groups_str = str(data_row.get('Qty', "")).split(';')
#             case_qtys_groups_str = str(data_row.get('Case qty', "")).split(';')
#
#             if not (len(items_groups_str) == len(qtys_groups_str) == len(case_qtys_groups_str)):
#                 print(
#                     f"Warning: Mismatch in the number of ';'-separated groups in row {row_num_in_sheet}. Skipping this row.")
#                 continue
#
#             # --- Step 2: Process each LPN Group to create LPN definitions ---
#             lpn_definitions = []
#             is_row_valid = True
#             for item_group, qty_group, case_qty_group in zip(items_groups_str, qtys_groups_str, case_qtys_groups_str):
#                 items = [item.strip() for item in item_group.split('@') if item.strip()]
#
#                 if not items:
#                     continue
#
#                 try:
#                     qtys = [int(qty.strip()) for qty in qty_group.split('@') if qty.strip()]
#                     case_qtys = [int(cq.strip()) for cq in case_qty_group.split('@') if cq.strip()]
#                 except ValueError as e:
#                     print(
#                         f"Error: Invalid number in row {row_num_in_sheet}. Ensure all values are integers. Details: {e}")
#                     is_row_valid = False
#                     break
#
#                 if not (len(items) == len(qtys) == len(case_qtys)):
#                     print(
#                         f"Warning: Mismatch in '@'-separated values for group '{item_group}' in row {row_num_in_sheet}. Skipping this group.")
#                     continue
#
#                 # --- Calculate number of LPNs for this definition ---
#                 num_lpns_to_generate = 0
#                 if case_qtys[0] > 0:
#                     num_lpns_to_generate = qtys[0] // case_qtys[0]
#
#                 # For mixed LPNs, validate that the LPN count is consistent for all items
#                 is_mixed = len(items) > 1
#                 if is_mixed:
#                     for j in range(1, len(items)):
#                         if case_qtys[j] == 0 or (qtys[j] // case_qtys[j]) != num_lpns_to_generate:
#                             print(
#                                 f"Error: Inconsistent Qty/CaseQty ratio for mixed LPN group '{item_group}' in row {row_num_in_sheet}. All items in a mixed group must result in the same number of LPNs. Skipping group.")
#                             num_lpns_to_generate = 0  # Invalidate this group
#                             break
#
#                 if num_lpns_to_generate > 0:
#                     lpn_definitions.append({
#                         "is_mixed": is_mixed,
#                         "items": items,
#                         "case_qtys": case_qtys,  # This is the quantity per item *inside one LPN*
#                         "num_lpns_to_generate": num_lpns_to_generate
#                     })
#
#             if not is_row_valid:
#                 continue
#
#             # --- Step 3: Generate ASN IDs for the current row ---
#             if not lpn_definitions:
#                 print(f"Warning: No valid LPN definitions found in row {row_num_in_sheet}. Skipping.")
#                 continue
#
#             asn_ids_for_this_row = self._generate_unique_asn_ids(num_of_asn, envn)
#             if not asn_ids_for_this_row:
#                 print(f"Skipping row {row_num_in_sheet} as no ASN IDs were generated (Number of ASN might be 0).")
#                 continue
#             self.all_generated_asn_ids.extend(asn_ids_for_this_row)
#
#             # --- Step 4: Distribute LPNs and build payloads ---
#             for asn_index, current_asn_id in enumerate(asn_ids_for_this_row):
#                 lpn_list_for_current_asn = []
#                 print(f"  ASN {current_asn_id}:")
#
#                 for lpn_def in lpn_definitions:
#                     total_lpns_for_def = lpn_def['num_lpns_to_generate']
#
#                     # Distribute LPNs for this definition evenly across the ASNs
#                     lpns_in_this_asn = total_lpns_for_def // num_of_asn
#                     if asn_index < (total_lpns_for_def % num_of_asn):
#                         lpns_in_this_asn += 1
#
#                     if lpns_in_this_asn > 0:
#                         item_desc = "@".join(lpn_def['items'])
#                         lpn_type = "Mixed-Item" if lpn_def['is_mixed'] else "Single-Item"
#                         print(f"    - {lpn_type} Group '{item_desc}': Generating {lpns_in_this_asn} LPNs.")
#
#                     for _ in range(lpns_in_this_asn):
#                         lpn_number_gen = NumberGeneration()
#                         current_lpn_id = lpn_number_gen.lpn_number_generation(envn)
#
#                         # Build the LpnDetail list, which may contain one or more items
#                         lpn_detail_list = []
#                         for item_id, case_qty in zip(lpn_def['items'], lpn_def['case_qtys']):
#                             lpn_detail_list.append({
#                                 "AsnId": current_asn_id, "ExpiryDate": "", "InventoryAttribute1": "01000",
#                                 "CountryOfOrigin": "CN", "ItemId": item_id, "ManufacturingDate": "",
#                                 "QuantityUomId": "LPN", "ShipByDate": "", "ShippedQuantity": case_qty,
#                                 "PurchaseOrderId": "25050501", "PurchaseOrderLineId": ""
#                             })
#
#                         lpn_extended = {"LpnHeight": "12", "LpnWidth": "12", "LpnLength": "24",
#                                         "LpnVendor": "0005005401"}
#
#                         lpn_data = {
#                             "AsnId": current_asn_id, "VendorId": None, "LpnId": current_lpn_id,
#                             "LpnStatus": "1000", "OrgId": plant,
#                             "SingleItemLPN": "0" if lpn_def['is_mixed'] else "1",
#                             "LpnTypeId": "ILPN", "Extended": lpn_extended, "LpnDetail": lpn_detail_list
#                         }
#                         lpn_list_for_current_asn.append(lpn_data)
#
#                 misc_nbr = NumberGeneration()
#                 bol, pro, trailer, seal = misc_nbr.misc_nbr(envn=envn)
#                 ASN_Extended = {"BolNumber": bol, "ProNumber": pro, "SealNumber": seal}
#
#                 if lpn_list_for_current_asn:
#                     asn_payload = {
#                         "AsnId": current_asn_id, "AsnOriginTypeId": "P", "OriginFacilityId": str(o_facility) ,"VendorId": None,
#                         "OrgId": str(plant), "DestinationFacilityId": str(plant),
#                         "AsnStatus": "1000", "AsnLevel": "LPN", "TrailerId": str(trailer), "Extended": ASN_Extended, "Lpn": lpn_list_for_current_asn
#                     }
#                     self.all_asn_payloads.append({'payload': asn_payload, 'environment': envn})
#
#         print(self.all_asn_payloads)
#
#         print(f"\n--- Generation Complete. Total Payloads Created: {len(self.all_asn_payloads)} ---")
#         return self.all_asn_payloads

# # Version 2
# from J30.Payload_generation.Worksheet_extract import Worksheet
# from J30.Payload_generation.Number_Generation import number_generation
#
#
# # --- Main Class for ASN Payload Generation ---
# class Asn_Payload_Generator:
#     def __init__(self):
#         """Initializes the generator."""
#         # Initiating the worksheet object
#         self.worksheet = Worksheet()
#         # These lists will accumulate all results from all processed rows.
#         self.all_generated_asn_ids = []
#         self.all_asn_payloads = []
#
#     def _generate_unique_asn_ids(self, num_of_asn_to_generate: int, envn: str) -> list:
#         """Generates a list of unique ASN IDs."""
#         asn_number = number_generation()
#         # This method is only responsible for generating and returning the numbers.
#         return asn_number.asn_number_generation(num_of_asn_to_generate, envn)
#
#     def generate_payloads(self) -> list:
#         """
#         Orchestrates the entire process. It fetches data from the worksheet,
#         iterates through each data row, handles single or multiple items per row,
#         generates the required ASNs and LPNs, and returns a final list of all
#         generated JSON payloads.
#         """
#         # Step 1: Get the list of data dictionaries from the worksheet.
#         try:
#             list_of_worksheet_dict = self.worksheet.create_asn_extract_parameters()
#             if list_of_worksheet_dict is None:
#                 print("Error: Worksheet method returned None. Expected a list. Halting generation.")
#                 return []
#         except Exception as e:
#             print(f"An unexpected error occurred while extracting data from the worksheet: {e}")
#             return []
#
#         if not list_of_worksheet_dict:
#             print("No data rows found in the worksheet to process.")
#             return []
#
#         print(f"Successfully extracted {len(list_of_worksheet_dict)} data row(s) for processing.")
#         # Clear previous results before a new run
#         self.all_asn_payloads = []
#         self.all_generated_asn_ids = []
#
#         # Step 2: Loop through each dictionary (each row from Excel) and process it completely.
#         for i, data_row in enumerate(list_of_worksheet_dict):
#             row_num_in_sheet = i + 2  # For clearer logging (assuming header is row 1)
#             print(f"\n--- Processing Excel Row {row_num_in_sheet} ---")
#
#             # Extract common parameters for the CURRENT row
#             plant = data_row.get("Plant")
#             num_of_asn = int(data_row.get('Number of ASN', 0))
#             envn = data_row.get("Environment")
#
#             # --- Handle single or multiple items, quantities, and case quantities ---
#             items_str = str(data_row.get("Item", ""))
#             qtys_str = str(data_row.get('Qty', ""))
#             case_qtys_str = str(data_row.get('Case qty', ""))
#
#             items = [item.strip() for item in items_str.split(';') if item.strip()]
#
#             try:
#                 qtys = [int(qty.strip()) for qty in qtys_str.split(';') if qty.strip()]
#                 case_qtys = [int(cq.strip()) for cq in case_qtys_str.split(';') if cq.strip()]
#             except ValueError as e:
#                 print(
#                     f"Error: Invalid number in 'Qty' or 'Case qty' field in row {row_num_in_sheet}. Please ensure all values are integers. Details: {e}")
#                 continue  # Skip to the next row
#
#             # Validate that the number of items, qtys, and case_qtys match
#             if not (len(items) == len(qtys) == len(case_qtys)):
#                 print(
#                     f"Warning: Mismatch in the number of semicolon-separated values in row {row_num_in_sheet}. Skipping this row.")
#                 print(f"  - Found {len(items)} Items: {items}")
#                 print(f"  - Found {len(qtys)} Qtys: {qtys}")
#                 print(f"  - Found {len(case_qtys)} Case Qtys: {case_qtys}")
#                 continue
#
#             if not items:
#                 print(f"Warning: No items found in row {row_num_in_sheet}. Skipping.")
#                 continue
#
#             print(f"Row {row_num_in_sheet}: Plant={plant}, Num_ASNs={num_of_asn}, Items={items}")
#
#             # Step 3: Generate ASN IDs specifically for the CURRENT row
#             asn_ids_for_this_row = self._generate_unique_asn_ids(num_of_asn, envn)
#             if not asn_ids_for_this_row:
#                 print(f"Skipping row {row_num_in_sheet} as no ASN IDs were generated (Number of ASN might be 0).")
#                 continue
#             self.all_generated_asn_ids.extend(asn_ids_for_this_row)
#
#             # Step 4: Calculate total LPNs needed per item for this entire row
#             total_lpns_per_item = []
#             for item, qty, case_qty in zip(items, qtys, case_qtys):
#                 if case_qty <= 0:
#                     print(
#                         f"Warning: 'Case qty' is zero or less for item {item} in row {row_num_in_sheet}. This item will have 0 LPNs.")
#                     total_lpns_per_item.append(0)
#                 else:
#                     total_lpns_for_one_item = int(qty / case_qty)
#                     total_lpns_per_item.append(total_lpns_for_one_item)
#
#             # Step 5: Distribute LPNs and build payloads for the CURRENT row
#             for asn_index, current_asn_id in enumerate(asn_ids_for_this_row):
#                 lpn_list_for_current_asn = []
#                 print(f"  ASN {current_asn_id}:")
#
#                 # For each item, calculate how many LPNs it gets in THIS ASN
#                 for item_index, item_id in enumerate(items):
#                     total_lpns_for_this_item = total_lpns_per_item[item_index]
#                     current_case_qty = case_qtys[item_index]
#
#                     if total_lpns_for_this_item == 0:
#                         continue  # Skip if no LPNs for this item
#
#                     # Distribute LPNs for this item evenly across the ASNs
#                     num_lpns_for_this_item_in_this_asn = total_lpns_for_this_item #// num_of_asn
#                     # Add the remainder LPNs to the first few ASNs
#                     if asn_index < (total_lpns_for_this_item % num_of_asn):
#                         num_lpns_for_this_item_in_this_asn += 1
#
#                     if num_lpns_for_this_item_in_this_asn > 0:
#                         print(f"    - Item {item_id}: Generating {num_lpns_for_this_item_in_this_asn} LPNs.")
#
#                     # Generate the required number of LPNs for this item in this ASN
#                     for _ in range(num_lpns_for_this_item_in_this_asn):
#                         lpn_number_gen = number_generation()
#                         current_lpn_id = lpn_number_gen.lpn_number_generation(envn)
#
#                         lpn_detail_data = {
#                             "AsnId": current_asn_id,
#                             "ExpiryDate": "",
#                             "InventoryAttribute1": "01000",
#                             "CountryOfOrigin": "CN",
#                             "ItemId": item_id,
#                             "ManufacturingDate": "",
#                             "QuantityUomId": "LPN",
#                             "ShipByDate": "",
#                             "ShippedQuantity": current_case_qty,
#                             "PurchaseOrderId": "25050501",
#                             "PurchaseOrderLineId": ""
#                         }
#
#                         lpn_data = {
#                             "AsnId": current_asn_id,
#                             "VendorId": None,
#                             "LpnId": current_lpn_id,
#                             "LpnStatus": "1000",
#                             "OrgId": plant,
#                             "SingleItemLPN": "1",
#                             "LpnTypeId": "ILPN",
#                             "LpnDetail": [lpn_detail_data]
#                         }
#                         lpn_list_for_current_asn.append(lpn_data)
#
#                 # Construct the full payload for the current ASN if it has LPNs
#                 if lpn_list_for_current_asn:
#                     asn_payload = {
#                         "AsnId": current_asn_id,
#                         "AsnOriginTypeId": "P",
#                         "VendorId": None,
#                         "OrgId": str(plant),
#                         "DestinationFacilityId": str(plant),
#                         "AsnStatus": "1000",
#                         "AsnLevel": "LPN",
#                         "Lpn": lpn_list_for_current_asn
#                     }
#                     payload_package = {
#                         'payload': asn_payload,
#                         'environment': envn
#                     }
#                     self.all_asn_payloads.append(payload_package)
#
#         print(f"\n--- Generation Complete. Total Payloads Created: {len(self.all_asn_payloads)} ---")
#         return self.all_asn_payloads


# # Version 1
#
# from J30.Payload_generation.Worksheet_extract import Worksheet
# from J30.Payload_generation.Number_Generation import number_generation
#
# # --- Main Class for ASN Payload Generation ---
# class Asn_Payload_Generator:
#     def __init__(self):
#         # Initiating the worksheet object
#         self.worksheet = Worksheet()
#         # These lists will accumulate all results from all processed rows.
#         self.all_generated_asn_ids = []
#         self.all_asn_payloads = []
#         # self.all_generated_lpn_id = {}
#         # self.stored_asn_id = {}
#
#     def _extract_parameters(self):
#         self.list_of_datadict = self.worksheet.create_asn_extract_parameters()
#         print(self.list_of_datadict)
#         try:
#             if not self.list_of_datadict:
#                 print(
#                     "The worksheet data didn't return the list of ASN dictionary therefore check the worksheet class.")
#         except Exception as e:
#             print(f"An unexpected error occurred while reading or extracting data: {e}")
#             return False
#         print(self.list_of_datadict)
#
#         for entry in self.list_of_datadict:
#             self.plant = entry.get("Plant")
#             self.num_of_asn = int(entry.get('Number of ASN', 0))
#             self.item = entry.get("Item")
#             self.qty = int(entry.get('Qty', 0))
#             self.case_qty = int(entry.get('Case qty', 1))
#             self.envn = entry.get("Environment")
#         return None
#
#     def _generate_unique_asn_ids(self, num_of_asn_to_generate: int, envn: str) -> list:
#
#         asn_number = number_generation()
#         generated_asn_ids = asn_number.asn_number_generation(num_of_asn_to_generate, envn)
#         self.all_generated_asn_ids.extend(generated_asn_ids)
#         # self.stored_asn_id[envn] = generated_asn_ids # Used for ASN search in different module.
#         return generated_asn_ids
#
#
#     def generate_payloads(self) -> list:
#         """
#         Orchestrates the entire process. It fetches data from the worksheet,
#         iterates through each data row, generates the required ASNs and LPNs,
#         and returns a final list of all generated JSON payloads.
#         """
#         # Step 1: Get the list of data dictionaries from the worksheet.
#         try:
#             list_of_datadict = self.worksheet.create_asn_extract_parameters()
#             # CRITICAL FIX: Ensure we have a list to iterate over, even if it's empty.
#             if list_of_datadict is None:
#                 print("Error: Worksheet method returned None. Expected a list. Halting generation.")
#                 return []
#         except Exception as e:
#             print(f"An unexpected error occurred while extracting data from the worksheet: {e}")
#             return []
#
#         if not list_of_datadict:
#             print("No data rows found in the worksheet to process.")
#             return []
#
#         print(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")
#         # Clear previous results before a new run
#         self.all_asn_payloads = []
#         self.all_generated_asn_ids = []
#         lpn_unique_counter = 0  # Ensures unique LPN IDs across ALL payloads
#
#
#         # Step 2: Loop through each dictionary (each row from Excel) and process it completely.
#         for i, data_row in enumerate(list_of_datadict):
#             # Extract parameters for the CURRENT row into local variables
#             plant = data_row.get("Plant")
#             num_of_asn = int(data_row.get('Number of ASN', 0))
#             item = data_row.get("Item")
#             qty = int(data_row.get('Qty', 0))
#             case_qty = int(data_row.get('Case qty', 1))
#             envn = data_row.get("Environment")  # Extracted but not currently used in payload
#
#             if case_qty == 0:
#                 print(f"Warning: 'Case qty' is zero for item {item} in row {i + 1}. Defaulting to 1 to avoid errors.")
#                 case_qty = 1
#
#             print(f"\n--- Processing Row {i + 1}: Plant={plant}, Item={item}, Num_ASNs={num_of_asn} ---")
#
#
#         # Step 3: Generate ASN IDs specifically for the CURRENT row
#             asn_ids_for_this_row = self._generate_unique_asn_ids(num_of_asn, envn)
#             if not asn_ids_for_this_row:
#                 print(f"Skipping this data row as no ASN IDs were generated.")
#                 continue  # Move to the next dictionary in the list
#             self.all_generated_asn_ids.extend(asn_ids_for_this_row)
#
#         # Step 4: Calculate LPNs and build payloads for the CURRENT row
#             num_of_lpn_total = int(qty / case_qty) * num_of_asn
#
#             for asn_index, current_asn_id in enumerate(asn_ids_for_this_row):
#                 lpn_list_for_current_asn = []
#                 # Distribute LPNs evenly across the ASNs for this row
#                 num_lpns_for_this_asn = num_of_lpn_total // num_of_asn
#                 if asn_index < (num_of_lpn_total % num_of_asn):
#                     num_lpns_for_this_asn += 1
#
#                 print(f"  ASN {current_asn_id}: Generating {num_lpns_for_this_asn} LPNs.")
#
#                 for _ in range(num_lpns_for_this_asn):
#                     # Generate a unique LPN ID for each LPN
#                     lpn_number = number_generation()
#                     current_lpn_id = lpn_number.lpn_number_generation(envn)
#                     # self.all_generated_lpn_id[envn] = current_lpn_id
#
#                     lpn_detail_data = {
#                         "AsnId": current_asn_id,
#                         "ExpiryDate": "",
#                         "InventoryAttribute1": "01000",
#                         "CountryOfOrigin": "CN",
#                         "ItemId": item,
#                         "ManufacturingDate": "",
#                         "QuantityUomId": "LPN",
#                         "ShipByDate": "",
#                         "ShippedQuantity": case_qty, # Quantity in this specific LPN
#                         "PurchaseOrderId": "25050501", # Static for now
#                         "PurchaseOrderLineId": "" # Static for now
#                     }
#
#                     lpn_data = {
#                         "AsnId": current_asn_id,
#                         "VendorId": None,
#                         "LpnId": current_lpn_id,
#                         "LpnStatus": "1000",
#                         "OrgId": plant,
#                         "SingleItemLPN": "1",
#                         "LpnTypeId": "ILPN",
#                         "LpnDetail": [lpn_detail_data] # Each LPN has a list of details (usually one item type per LPN here)
#                     }
#                     lpn_list_for_current_asn.append(lpn_data)
#
#                 # Construct the full payload for the current ASN
#                 asn_payload = {
#                     "AsnId": current_asn_id,
#                     "AsnOriginTypeId": "P",
#                     "VendorId": None,
#                     "OrgId": str(plant),
#                     "DestinationFacilityId": str(plant), # Static for now
#                     "AsnStatus": "1000",
#                     "AsnLevel": "LPN",
#                     "Lpn": lpn_list_for_current_asn # List of LPNs for this ASN
#                 }
#                 payload_package = {
#                     'payload': asn_payload,
#                     'environment': envn
#                 }
#                 self.all_asn_payloads.append(payload_package)
#
#             print(f"\n--- Generation Complete. Total Payloads Created: {len(self.all_asn_payloads)} ---")
#
#         return self.all_asn_payloads

# ---
# ## How to Use the Class
#
# Here's how you'd use this `AsnPayloadGenerator` class in your main script:
#
# ```python
# if __name__ == "__main__":
#     # Create an instance of the generator
#     # Make sure 'WorkSheet.xlsx' exists in the same directory or provide the full path
#     asn_gen = AsnPayloadGenerator('WorkSheet.xlsx')
#
#     # Get the bearer token
#     bearer_token = asn_gen.get_bearer_token()
#     print(f"\nGenerated Bearer Token: {bearer_token}")
#
#     # Generate all the ASN payloads
#     generated_payloads = asn_gen.generate_payloads()
#
# # Print out each generated payload
# if generated_payloads:
#     for i, payload in enumerate(generated_payloads):
#         # Access the ASN ID from the generator's internal list for printing context
#         current_asn_id_for_print = asn_gen.asn_ids[i] if i < len(asn_gen.asn_ids) else "N/A"
#         print(f"\n--- Payload for ASN {i+1} ({current_asn_id_for_print}) ---")
#         print(payload)
# else:
#     print("\nNo payloads were generated. Please check your Excel input and generator logic.")


# Using current date (July 2025) and appending a counter for uniqueness
# current_lpn_id = f'0000VG{datetime.today().strftime('%d%m%Y')}{envn}{random.randint(1000, 9999)}{lpn_unique_counter:04d}'
# lpn_unique_counter += 1


# Successful Execution output.
# /Users/vgana3/Documents/Pycharm/MAWM/.venv/bin/python /Users/vgana3/Documents/Pycharm/MAWM/J30/ASN_Creation.py
# <pandas.io.excel._base.ExcelFile object at 0x10240d130>
# ['CreateASN', 'SearchASN']
# Sheets found in '/Users/vgana3/Documents/Pycharm/MAWM/J30/Payload_generation/WorkSheet.xlsx': ['CreateASN', 'SearchASN']
#
# Data from 'ASN' sheet:
#    Plant Environment  Number of ASN             Item  Qty  Case qty
# 0   1081         DEV              2  AC4081-014-MISC   12         6
# 1   1081          QA              2  AC4081-014-MISC   12         6
# [{'Plant': 1081, 'Environment': 'DEV', 'Number of ASN': 2, 'Item': 'AC4081-014-MISC', 'Qty': 12, 'Case qty': 6}, {'Plant': 1081, 'Environment': 'QA', 'Number of ASN': 2, 'Item': 'AC4081-014-MISC', 'Qty': 12, 'Case qty': 6}]
# Successfully extracted 2 data row(s) for processing.
#
# --- Processing Row 1: Plant=1081, Item=AC4081-014-MISC, Num_ASNs=2 ---
#   ASN VASN0607DEV9790: Generating 2 LPNs.
#   ASN VASN0607DEV3121: Generating 2 LPNs.
#
# --- Generation Complete. Total Payloads Created: 2 ---
#
# --- Processing Row 2: Plant=1081, Item=AC4081-014-MISC, Num_ASNs=2 ---
#   ASN VASN0607QA8020: Generating 2 LPNs.
#   ASN VASN0607QA1181: Generating 2 LPNs.
#
# --- Generation Complete. Total Payloads Created: 4 ---
#
# ==================== Processing 2 Payloads for Environment: DEV ====================
# Successfully retrieved token for DEV environment.
#
# --- [DEV] Processing Payload 1/2 for Plant 1081 ---
# Sending payload to URL: https://nikeaplawmdev1.sce.manh.com/receiving/api/receiving/asn/save
# -> Success: True, Message: None
#
# --- [DEV] Processing Payload 2/2 for Plant 1081 ---
# Sending payload to URL: https://nikeaplawmdev1.sce.manh.com/receiving/api/receiving/asn/save
# -> Success: True, Message: None
#
# ==================== Processing 2 Payloads for Environment: QA ====================
# Successfully retrieved token for QA environment.
#
# --- [QA] Processing Payload 1/2 for Plant 1081 ---
# Sending payload to URL: https://nikeaplawmqa1.sce.manh.com/receiving/api/receiving/asn/save
# -> Success: True, Message: None
#
# --- [QA] Processing Payload 2/2 for Plant 1081 ---
# Sending payload to URL: https://nikeaplawmqa1.sce.manh.com/receiving/api/receiving/asn/save
# -> Success: True, Message: None
#
# Process finished with exit code 0
