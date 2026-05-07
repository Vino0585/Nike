import logging
from typing import Any
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path

# Ensure project root is on sys.path so `Outbound` and `Inbound_payload_generation` packages can be imported
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent  # .../Nike/J30
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Outbound.Outbound_Payload_Generation.Outbound_Worksheet_Extract import Outbound_Worksheet
from Inbound.Inbound_payload_generation.Number_Generation import NumberGeneration

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Order_Creation_Payload:
    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_order_payloads = []
        self.po_nbr = self.number_gen.purchase_order_number()

    def _parse_order_line_item(self, item, qty, provider_service_id, vas_code_service_uom, row_num_in_sheet) -> list:
        item_grp = item.split(';')
        qty_grp = qty.split(';')
        vas_code_service_id_grp = provider_service_id.split(';')
        vas_code_service_uom_grp = vas_code_service_uom.split(';')

        if not (len(item_grp) == len(qty_grp) == len(vas_code_service_id_grp) == len(vas_code_service_uom_grp)):
            logging.error(
                f"WARNING: Mismatch in ';' -separated groups in row {row_num_in_sheet}. "
                f"Items: {len(item_grp)}, Qtys: {len(qty_grp)}, VAS IDs: {len(vas_code_service_id_grp)}, "
                f"VAS UOMs: {len(vas_code_service_uom_grp)}. Skipping this row's order lines."
            )
            return []



        order_line_list = []
        order_line_id = 1  # Initialize the line ID *before* the loop.
        for current_item, current_qty, current_vas_id_group, current_vas_uom_group in zip(item_grp, qty_grp, vas_code_service_id_grp, vas_code_service_uom_grp):
            extended = {
                "PurchaseOrderNumber": self.po_nbr, "DivisionCode": "20", "AlwaysAvailableIndicator": False,
                "ProductLifeCycleCode": "ACT", "LaunchCode": "N", "PromotionalIndicator": False,
                "MaterialAvailableDate": "2025-04-05T13:28:11", "PurchaseOrderLineNumber": "1",
                "SalesOrderLineNumber": "1", "BatchNumber": "084077890"
                }

            vas_code_service_ids = [vas_id.strip() for vas_id in current_vas_id_group.split('@') if vas_id.strip()]
            vas_code_service_uoms = [vas_uom.strip() for vas_uom in current_vas_uom_group.split('@') if vas_uom.strip()]

            if not (len(vas_code_service_ids) == len(vas_code_service_uoms)):
                logging.error(f"Mismatch in '@' in vase code service id and service uom in row {row_num_in_sheet}. Skipping this row's order lines.")
                return []

            # Use this line in future for VAS details to be included in OriginalOrderLineRequestedServices for now it is mentioned as empty list []
            vas_detail = []
            sequence_nbr = 1
            for vas_code_service_id, vas_code_service_uom in zip(vas_code_service_ids, vas_code_service_uoms):
                original_order_line_requested_service = {
                        "ServiceTypeId": 'VAS', "ProvidedServiceId": provider_service_id,
                        "Sequence": sequence_nbr, "ServiceUomId": vas_code_service_uom
                    }
                vas_detail.append(original_order_line_requested_service)
                sequence_nbr += 1

            order_line = {
                     "CountryOfOriginId": "",
                     "OriginalOrderLineId": str(order_line_id),
                     "ItemId": current_item,
                     "OrderedQuantity": current_qty,
                     "QuantityUomId": " Unit", "ItemAttribute1": "01000", "UnitPrice": "32.5",
                    # Add the vas_detail here without the list parameter as it is already a list in RequestedServices
                     "Extended": extended, "OriginalOrderLineRequestedServices": vas_detail
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
            phone = data_row.get("phone")
            country = data_row.get("country")
            first_name = data_row.get("first_name")
            if pd.isna(first_name):
                first_name = None
            email = data_row.get("email")
            if pd.isna(email):
                email = None
            item = data_row.get("item")
            qty = str(data_row.get("qty"))
            d_facility = data_row.get("d_facility")
            pre_pack_code = data_row.get("pre_pack_code")
            provider_service_id = data_row.get("provider_service_id", 'BOX')
            vas_code_service_uom = data_row.get("vas_code_service_uom", 'oLPN')
            carrier_code = data_row.get("carrier_code")
            hub_code = data_row.get("hub_code")
            route_number_raw = data_row.get("route_number")
            # Default to empty string if None or NaN
            route_number = '' if (route_number_raw is None or pd.isna(route_number_raw)) else str(route_number_raw)
            mark_for_customer_id_raw = data_row.get("mark_for_customer_id")
            # Default to empty string if None or NaN
            mark_for_customer_id = '' if (mark_for_customer_id_raw is None or pd.isna(mark_for_customer_id_raw)) else str(mark_for_customer_id_raw)
            sold_to_facility_id = data_row.get("sold_to_facility_id")

            now = datetime.now()
            now_iso = now.isoformat(timespec='seconds')
            now_end = now + timedelta(days=4)
            now_end_iso = now_end.isoformat(timespec='seconds')
            future = now + timedelta(days=10)
            future_iso = future.isoformat(timespec='seconds')
            future_end = future + timedelta(days=20)
            future_end_iso = future_end.isoformat(timespec='seconds')
            scheduled_delivery_date = None

            order_ids = self.number_gen.order_number_generation(num_of_order, envn, user_initial)

            if not order_ids:
                logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Number of Orders' is 0 or invalid entry is given")
                continue

            for order_index, current_order_id in enumerate(order_ids):
                logging.info(f"Order: {current_order_id}")

                dest_address = {
                    "Address1": address_1, "City": city, "State": state, "PostalCode": postal_code,
                    "Country": country, "FirstName": first_name, "Email": email, "Phone": phone
                }

                bill_address = {
                    "Address1": address_1, "City": city, "State": state, "PostalCode": postal_code,
                    "Country": country,  "Phone": phone
                }

                # Default ShippingPointCode to empty string if plant is None or NaN
                shipping_point_code = '' if (plant is None or pd.isna(plant)) else str(plant)
                if order_type == 'Z033':
                    extended = {
                        "FulfillmentRequestType": "ZLF", "ServiceLevelCode": service_level, "ShippingPointCode": shipping_point_code,
                        "RouteNumber": route_number, "TransitTime": "01", "SalesOrganisationCode": "2000",
                        "ExportIndicator": False, "ShipToAddressOverrideIndicator": False,
                        "CustomerDocumentRequiredIndicator": False, "PoRequiredIndicator": False,
                        "AppointmentSchedulingIndicator": False, "SalesDeliveryPriority": "2", "TotalVasTime": "0.0",
                        "ConsolFlag": False, "CarrierServiceCode": carrier_code,  "CarrierHubCode": hub_code,
                        "ScheduledDeliveryEndDate": future_end_iso,
                        "DeliveryByTheHour": "00000000", "CustomerRequestedTimestamp": future_iso,
                        "SoldToFacilityId": sold_to_facility_id,
                        "SoldToBillingAccountNumber": sold_to_facility_id, "MarkForCustomerId": f"{mark_for_customer_id}",
                        "DestinationFacilityName": "NIKE STORE LE MARAIS",
                        "MarkForCustomerName": "NIKE STORE LE MARAIS", "DestinationContactName": "",
                        "SalesOrderNumber": "8365566199", "ExternalPurchaseOrderNumber": self.po_nbr,
                        "CustomerBusinessTypeCode": "4", "CustomerAccountType": "9", "ChannelClassCode": "26",
                        "DeliveryEndDateTime": future_end_iso, "Priority": 10, "CarrierCode": carrier_code,
                        "ShipToPartyIdentifierType": "WHOLE_SALE_DC", "LastShipmentTimestamp": future_iso,
                        "DeliveryStartDateTime": future_iso, "PackSlipRequired": "N", "ReturnsLabelRequired": "N"
                    }
                else:
                    extended = {
                        "FulfillmentRequestType": "ZLF", "ServiceLevelCode": service_level, "ShippingPointCode": shipping_point_code,
                        "RouteNumber": route_number, "TransitTime": "01", "SalesOrganisationCode": "2000",
                        "ExportIndicator": False, "ShipToAddressOverrideIndicator": False,
                        "CustomerDocumentRequiredIndicator": False, "PoRequiredIndicator": False,
                        "AppointmentSchedulingIndicator": False, "SalesDeliveryPriority": "2", "TotalVasTime": "0.0",
                        "ConsolFlag": False, "CarrierServiceCode": carrier_code,  "CarrierHubCode": hub_code,
                        "DeliveryByTheHour": "00000000", "CustomerRequestedTimestamp": future_iso,
                        "SoldToFacilityId": sold_to_facility_id,
                        "SoldToBillingAccountNumber": sold_to_facility_id, "MarkForCustomerId": f"{mark_for_customer_id}",
                        "DestinationFacilityName": "NIKE STORE LE MARAIS",
                        "MarkForCustomerName": "NIKE STORE LE MARAIS", "DestinationContactName": "",
                        "SalesOrderNumber": "8365566199", "ExternalPurchaseOrderNumber": self.po_nbr,
                        "CustomerBusinessTypeCode": "4", "CustomerAccountType": "9", "ChannelClassCode": "26",
                        "DeliveryEndDateTime": future_end_iso, "Priority": 10, "CarrierCode": carrier_code,
                        "ShipToPartyIdentifierType": "WHOLE_SALE_DC", "LastShipmentTimestamp": future_iso,
                        "DeliveryStartDateTime": future_iso, "PackSlipRequired": "N", "ReturnsLabelRequired": "N"
                    }

                order_line_info = self._parse_order_line_item(item, qty, provider_service_id, vas_code_service_uom, row_num_in_sheet)

                origin_facility_id = '' if (plant is None or pd.isna(plant)) else str(plant)
                order_payload = {
                    "OrderType": order_type, "OriginFacilityId": origin_facility_id, "OriginalOrderId": current_order_id,
                    "IncotermId": "DDP", "ResidentialDestination": True,
                    "MaximumStatus": "0500", "MinimumStatus": "0500",
                    "PickupStartDateTime": now_iso, "PickupEndDateTime": now_end_iso,
                    "DeliveryStartDateTime": future_iso, "DeliveryEndDateTime": future_end_iso,
                    "DestinationFacilityId": d_facility, "DestinationAddress":  dest_address,
                    "BillToFacilityId": sold_to_facility_id, "BillToName": "NIKE STORE LE MARAIS", 
                    "BillToAddress": bill_address,
                    "Extended": extended,
                    "OriginalOrderLine": order_line_info
                }
                self.all_order_payloads.append({'payload': order_payload, 'environment': envn, 'plant': plant})
        # This return must be outside the main for-loop to process all rows from the sheet.
        return self.all_order_payloads

# This block is excellent for testing your class in isolation.
if __name__ == "__main__":
    order_generation = Order_Creation_Payload()
    final_payloads = order_generation.generate_payloads
    # Optional: Pretty-print the first payload for verification
    if final_payloads:
        import json
        for i, payloads in enumerate(final_payloads):
            num = i+1
            logging.info(f"No {num} Generated Payload")
            print(json.dumps(payloads, indent=2))