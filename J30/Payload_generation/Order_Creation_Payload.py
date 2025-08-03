import logging
from typing import Any
from datetime import datetime, timedelta

from Payload_generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Payload_generation.Number_Generation import NumberGeneration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Order_Creation_Payload:
    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_order_payloads = []

    def _parse_order_line_item(self, item, qty, vas_code_service_id, vas_code_service_uom, row_num_in_sheet) -> list:
        item_grp = item.split(';')
        qty_grp = qty.split(';')
        vas_code_service_id_grp = vas_code_service_id.split(';')
        vas_code_service_uom_grp = vas_code_service_uom.split(';')

        # If a single VAS code/UOM is provided for multiple items, duplicate it to match the item count.
        # This prevents zip() from truncating the loop prematurely.
        num_items = len(item_grp)
        if len(vas_code_service_id_grp) == 1 and num_items > 1:
            vas_code_service_id_grp = vas_code_service_id_grp * num_items
        if len(vas_code_service_uom_grp) == 1 and num_items > 1:
            vas_code_service_uom_grp = vas_code_service_uom_grp * num_items

        # A more robust check to ensure all lists have the same length before zipping.
        if not (len(item_grp) == len(qty_grp) == len(vas_code_service_id_grp) == len(vas_code_service_uom_grp)):
            logging.error(
                f"WARNING: Mismatch in ';' -separated groups in row {row_num_in_sheet}. "
                f"Items: {len(item_grp)}, Qtys: {len(qty_grp)}, VAS IDs: {len(vas_code_service_id_grp)}, "
                f"VAS UOMs: {len(vas_code_service_uom_grp)}. Skipping this row's order lines."
            )
            return []

        order_line_list = []
        order_line_id = 1  # Initialize the line ID *before* the loop.
        for item_grp, qty_grp, vas_code_service_id_grp, vas_code_service_uom_grp in zip(item_grp, qty_grp, vas_code_service_id_grp, vas_code_service_uom_grp):
            extended = {
                "PurchaseOrderNumber": "TOC65312052", "DivisionCode": "20", "AlwaysAvailableIndicator": False,
                "ProductLifeCycleCode": "ACT", "LaunchCode": "N", "PromotionalIndicator": False,
                "MaterialAvailableDate": "2025-04-05T13:28:11", "PurchaseOrderLineNumber": "1",
                "SalesOrderLineNumber": "1", "BatchNumber": "065312052"
                }

            original_order_line_requested_service = [
                {
                    "ServiceTypeId": 'VAS',
                    "ProvidedServiceId": vas_code_service_id_grp,
                    "Sequence": "1",
                    "ServiceUomId": vas_code_service_uom_grp
                }
                ]

            order_line = {
                     "OriginalOrderLineId": order_line_id,
                     "ItemId": item_grp,
                     "OrderedQuantity": qty_grp,
                     "QuantityUomId": "Unit",
                     "ItemAttribute1": "01000",
                     "UnitPrice": "32.5",
                     "CountryOfOriginId": "ID",
                     "Extended": extended,
                     "OriginalOrderLineRequestedService": original_order_line_requested_service
                         }

            order_line_list.append(order_line)
            order_line_id += 1

        return order_line_list

    @property
    def generate_payloads(self) -> list[Any]:
        try:
            list_of_datadict = self.worksheet.create_order_extract_parameters()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation.")
                return []  # Return empty list on failure
        except Exception as e:
            logging.error(f"Error: {e}")
            return []

        logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

        self.all_order_payloads = []

        for i, data_row in enumerate(list_of_datadict):
            row_num_in_sheet = i + 1
            logging.info(f"Processing Excel Row {row_num_in_sheet}")

            plant = data_row.get("plant")
            envn = data_row.get("environment")
            user_initial = data_row.get("initial")
            num_of_order = data_row.get("number_of_Orders")
            order_type = data_row.get("order_Type")
            service_level = data_row.get("service_level")
            address_1 = data_row.get("address_1")
            city = data_row.get("city")
            state = data_row.get("state")
            postal_code = data_row.get("postal_code")
            country = data_row.get("country")
            first_name = data_row.get("first_name")
            email = data_row.get("email")
            item = data_row.get("item")
            qty = str(data_row.get("qty"))
            d_facility = str(data_row.get("d_facility"))
            pre_pack_code = data_row.get("pre_pack_code")
            vas_code_service_id = data_row.get("vas_code_service_id", 'BOX')
            vas_code_service_uom = data_row.get("vas_code_service_uom", 'oLPN')

            now = datetime.now()
            now_iso = now.isoformat(timespec='seconds')
            future = now + timedelta(days=5)
            future_iso = future.isoformat(timespec='seconds')

            order_ids = self.number_gen.order_number_generation(num_of_order, envn, user_initial)

            if not order_ids:
                logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Number of Orders' is 0 or invalid entry is given")
                continue

            for order_index, current_order_id in enumerate(order_ids):
                logging.info(f"Order {current_order_id}:")

                dest_address = {
                    "Address1": address_1, "City": city, "State": state, "PostalCode": postal_code,
                    "Country": country, "FirstName": first_name, "Email": email
                }

                extended = {
                    "FulfillmentRequestType": "ZLF", "ServiceLevelCode": service_level, "ShippingPointCode": plant,
                    "RouteNumber": "103002", "TransitTime": "01", "SalesOrganisationCode": "2000",
                    "ExportIndicator": False,
                    "ShipToAddressOverrideIndicator": False, "CustomerDocumentRequiredIndicator": False,
                    "AppointmentSchedulingIndicator": True, "SalesDeliveryPriority": "2", "TotalVasTime": "0.0",
                    "ConsolFlag": False, "CarrierServiceCode": "ZTRA", "ScheduledDeliveryEndDate": future_iso,
                    "DeliveryByTheHour": "00000000", "CustomerRequestedTimestamp": future_iso,
                    "SoldToFacilityId": "8000035",
                    "SoldToBillingAccountNumber": "300597", "MarkForCustomerId": "314896",
                    "DestinationFacilityName": "CHOCOLADE ECLAIRTJE",
                    "MarkForCustomerName": "CHOCOLADE ECLAIRTJE", "DestinationContactName": "",
                    "CarrierHubCode": "H590",
                    "SalesOrderNumber": "8365566199", "ExternalPurchaseOrderNumber": "EO8365566199",
                    "PoRequiredIndicator": False,
                    "CustomerBusinessTypeCode": "4", "CustomerAccountType": "9", "ChannelClassCode": "28",
                    "DeliveryEndDateTime": future_iso,
                    "Priority": 10, "CarrierCode": "UPSY", "ShipToPartyIdentifierType": "DIGITAL",
                    "LastShipmentTimestamp": future_iso,
                    "DeliveryStartDateTime": future_iso, "PackSlipRequired": "N", "ReturnsLabelRequired": "N"
                }

                order_line_info = self._parse_order_line_item(item, qty, vas_code_service_id, vas_code_service_uom, row_num_in_sheet)

                order_payload = {
                    "OrderType": order_type, "OriginFacilityId": plant, "OriginalOrderId": current_order_id,
                    "IncotermId": "DDP", "ResidentialDestination": True,
                    "MaximumStatus": "0500", "MinimumStatus": "0500",
                    "PickupEndDateTime": now_iso, "PickupStartDateTime": now_iso,
                    "DeliveryEndDateTime": future_iso, "DeliveryStartDateTime": future_iso,
                    "DestinationFacilityId": d_facility, "DestinationAddress":  dest_address,
                    "BillToFacilityId": d_facility, "BillToName": "CHOCOLADE ECLAIRTJE", "BillToAddress": dest_address,
                    "Extended": extended,
                    "OriginalOrderLine": order_line_info
                }
                self.all_order_payloads.append({'payload': order_payload, 'environment': envn, 'plant': plant})
        # This return must be outside the main for-loop to process all rows from the sheet.
        return self.all_order_payloads

# # This block is excellent for testing your class in isolation.
# if __name__ == "__main__":
#     order_generation = Order_Creation_Payload()
#     final_payloads = order_generation.generate_payloads
#     # Optional: Pretty-print the first payload for verification
#     if final_payloads:
#         import json
#         for i, payloads in enumerate(final_payloads):
#             num = i+1
#             logging.info(f"No {num} Generated Payload")
#             print(json.dumps(payloads, indent=2))