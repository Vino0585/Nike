import datetime
import logging
from Inbound.Payload_generation.Worksheet_extract import Worksheet
from Inbound.Payload_generation.Number_Generation import NumberGeneration

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
            logging.error(f"--> WARNING: Mismatch in ';'-separated groups in row {row_num_in_sheet}. Skipping.")
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
                    logging.error(
                        f"--> WARNING: Mismatch in '@'-separated values for group '{item_group}' in row {row_num_in_sheet}. Skipping group.")
                    continue

                num_lpns_to_generate = qtys[0] // case_qtys[0] if case_qtys and case_qtys[0] > 0 else 0
                is_mixed = len(items) > 1

                if is_mixed:
                    for j in range(1, len(items)):
                        if case_qtys[j] == 0 or (qtys[j] // case_qtys[j]) != num_lpns_to_generate:
                            logging.error(
                                f"--> ERROR: Inconsistent Qty/CaseQty ratio for mixed LPN group '{item_group}' in row {row_num_in_sheet}. Skipping group.")
                            num_lpns_to_generate = 0
                            break

                if num_lpns_to_generate > 0:
                    lpn_definitions.append({
                        "is_mixed": is_mixed, "items": items, "case_qtys": case_qtys,
                        "num_lpns_to_generate": num_lpns_to_generate
                    })
            except (ValueError, ZeroDivisionError) as e:
                logging.error(f"--> ERROR: Invalid data in row {row_num_in_sheet} for group '{item_group}'. Details: {e}")
                continue

        return lpn_definitions

    def _build_lpn_list_for_asn(self, lpn_definitions: list, num_of_asn: int, asn_index: int, current_asn_id: str,
                                envn: str, plant: str) -> list:
        """Builds the list of LPN JSON objects for a single ASN."""
        lpn_list_for_current_asn = []
        for lpn_def in lpn_definitions:
            total_lpns_for_def = lpn_def['num_lpns_to_generate']
            # lpns_in_this_asn = total_lpns_for_def // num_of_asn This will further divide it so this is wrong.
            if asn_index < (total_lpns_for_def % num_of_asn):
                total_lpns_for_def += 1

            if total_lpns_for_def > 0:
                item_desc = "@".join(lpn_def['items'])
                lpn_type = "Mixed-Item" if lpn_def['is_mixed'] else "Single-Item"
                logging.info(f"{lpn_type} Group '{item_desc}': Generating {total_lpns_for_def} LPNs.")

            current_po_id = self.number_gen.purchase_order_number()
            for _ in range(total_lpns_for_def):
                current_lpn_id = self.number_gen.lpn_number_generation(envn)
                lpn_detail_list = [
                    {
                        "AsnId": current_asn_id, "ExpiryDate": "", "InventoryAttribute1": "01000",
                        "CountryOfOrigin": "CN", "ItemId": item_id, "ManufacturingDate": "",
                        "QuantityUomId": "Unit", "ShipByDate": "", "ShippedQuantity": case_qty,
                        "PurchaseOrderId": current_po_id, "PurchaseOrderLineId": ""
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
                logging.error("Error: Worksheet method returned None. Halting generation.")
                return []
        except Exception as e:
            logging.error(f"An unexpected error occurred while extracting data from the worksheet: {e}")
            return []

        logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

        # **CRITICAL FIX**: Reset the list before each run.
        # This ensures that calling `generate_payloads` twice doesn't accumulate results.
        self.all_asn_payloads = []

        for i, data_row in enumerate(list_of_datadict):
            # Excel rows are 1-based and have a header, so the first data row is at index 0, but is row 2 in the sheet.
            row_num_in_sheet = i + 2
            logging.info(f"Processing Excel Row {row_num_in_sheet}")

            plant = data_row.get("Plant")
            num_of_asn = int(data_row.get('Number of ASN', 0))
            envn = data_row.get("Environment")
            o_facility = data_row.get("O_Facility", '0005005401')
            carrier_id = data_row.get("CarrierId", 'AUPU')
            initial = data_row.get("Initial", 'VG')

            lpn_definitions = self._parse_lpn_definitions_from_row(data_row, row_num_in_sheet)
            if not lpn_definitions:
                logging.info(f"INFO: No valid LPNs to generate for row {row_num_in_sheet}. Skipping.")
                continue

            asn_ids = self.number_gen.asn_number_generation(num_of_asn, envn, initial)
            if not asn_ids:
                logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Number of ASN' is 0.")
                continue

            for asn_index, current_asn_id in enumerate(asn_ids):
                logging.info(f"ASN {current_asn_id}:")
                lpn_list = self._build_lpn_list_for_asn(lpn_definitions, num_of_asn, asn_index, current_asn_id, envn,
                                                        plant)

                if lpn_list:
                    bol, pro, trailer, seal = self.number_gen.misc_nbr(envn=envn)
                    date_now = datetime.date.today().strftime("%Y-%m-%d")
                    date_now_utc = datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    asn_extended = {"BolNumber": bol, "ProNumber": pro, "SealNumber": seal, "ShipmentStart": date_now, "ShipmentCreateDate": date_now_utc}

                    asn_payload = {
                        "AsnId": current_asn_id, "AsnOriginTypeId": "P", "OriginFacilityId": o_facility,
                        "VendorId": None, "CarrierId": carrier_id, "BillOfLadingNumber": bol,
                        "ProNumber": pro, "OrgId": str(plant), "DestinationFacilityId": str(plant),
                        "AsnStatus": "1000", "AsnLevel": "LPN", "TrailerId": str(trailer), "Extended": asn_extended,
                        "Lpn": lpn_list
                    }
                    self.all_asn_payloads.append({'payload': asn_payload, 'environment': envn})

        logging.info(f"Generation Complete. Total Payloads Created: {len(self.all_asn_payloads)}")
        return self.all_asn_payloads


# This block is excellent for testing your class in isolation.
if __name__ == "__main__":
    asn_generator = Asn_Payload_Generator()
    final_payloads = asn_generator.generate_payloads
    # Optional: Pretty-print the first payload for verification
    if final_payloads:
        import json
        for i, payloads in enumerate(final_payloads):
            num = i+1
            logging.info(f"\n--- No {num} Generated Payload ---")
            print(json.dumps(payloads, indent=2))