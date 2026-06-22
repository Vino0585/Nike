import logging
from typing import Any
from datetime import datetime
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

class FR_Order_Creation_Payload:
    def __init__(self):
        self.worksheet = Outbound_Worksheet()
        self.number_gen = NumberGeneration()
        self.all_order_payloads = []
        self.po_nbr = self.number_gen.purchase_order_number()

    def _parse_order_line_item(self, item, qty, instruction_code, instruction_text,
                               order_type, row_num_in_sheet, plant, gtin, formatted_dlvd, fr_request_delivery_date, ) -> list:
        item_grp = item.split(';')
        qty_grp = qty.split(';')
        gtin_grp = gtin.split(';')
        instruction_code_grp = instruction_code.split(';')
        instruction_text_grp = instruction_text.split(';')
        order_type = order_type
        plant = plant
        product_life_cycle = ''
        if order_type != 'Z033':
            product_life_cycle = 'ACT'
        else:
            product_life_cycle = 'IAC'

        instruction_code_type = ''
        reference_ItemType_Description = ''

        if order_type != 'Z033':
            instruction_code_type = 'AIT'
            reference_ItemType_Description = ''
        else:
            instruction_code_type = 'AIS'
            reference_ItemType_Description = 'DTCJ'

        if not (len(item_grp) == len(qty_grp) == len(gtin_grp) == len(instruction_code_grp) == len(instruction_text_grp)):
            logging.error(
                f"WARNING: Mismatch in ';' -separated groups in row {row_num_in_sheet}. "
                f"Items: {len(item_grp)}, Qtys: {len(qty_grp)}, GTINs: {len(gtin_grp)} VAS IDs: {len(instruction_code_grp)}, "
                f"VAS UOMs: {len(instruction_text_grp)}. Skipping this row's order lines."
            )
            return []

        order_line_list = []
        order_line_id = 900001  # Initialize the line ID *before* the loop.
        for current_item, current_qty, current_gtin, current_instruction_code, current_instruction_text in zip(item_grp, qty_grp, gtin_grp, instruction_code_grp, instruction_text_grp):
            
            fulfillment_request_item_reference_order = [
                {"referenceItemTypeCode": "SALES_DOCUMENT_NUMBER", "referenceItemValue": "000010"},
                {"referenceItemTypeCode": "PURCHASE_ORDER_ITEM_NUMBER", "referenceItemValue": "1"}
            ]
            if reference_ItemType_Description != '':
                for reference_order_entry in fulfillment_request_item_reference_order:
                    reference_order_entry["referenceItemTypeDescription"] = reference_ItemType_Description

            fulfillment_request_Item = {
                "fulfilmentRequestItemNbr": str(order_line_id), "gtin": current_gtin, "shippingPointCode": plant,
                "materialNumber": current_item.rsplit('-', 1)[0], "divisionCode": "10", "poRequiredIndicator": False,
                "alwaysAvailableIndicator": False, "productLifecycleCode": product_life_cycle, "launchCode": "N",
                "materialGroupCode": "03", "storageLocationCode": "1000", "batchNumber": "0043754328", "prepackCode": "0",
                "promotionalIndicator": False, "customerBusinessTypeCode": "001", "customerAccountType": "009",
                "channelClassCode": "26", "netPriceAmount": 0, "manufacturersSuggestedRetailPrice": 48,
                "salesUnitQuantity": current_qty, "salesUnitQuantityUOM": "EA", "baseUnitQuantity": current_qty, "baseUnitQuantityUOM": "EA",
                "grossWeight": 1.104, "netWeight": 1.104, "weightUOM": "KG", "sizeCode": current_item.rsplit('-', 1)[1],
                "stockCategoryCode": "01000", "materialAvailableDate": "2026-06-16", "assortmentNumber": "0043754328",
                "fulfillmentRequestItemReferenceOrder": fulfillment_request_item_reference_order,
                "fulfillmentRequestItemDate": [
                    { "lastShipmentTimestamp": fr_request_delivery_date, "scheduledDeliveryEndTimestamp": fr_request_delivery_date,
                       "materialAvailableDate": "2026-06-19" }
                ]
                }

            current_instruction_code_id = [instruction_code.strip() for instruction_code in current_instruction_code.split('@') if instruction_code.strip()]
            current_instruction_text_id = [instruction_text.strip() for instruction_text in current_instruction_text.split('@') if instruction_text.strip()]

            if not (len(current_instruction_code_id) == len(current_instruction_text_id)):
                logging.error(f"Mismatch in '@' in vase code service id and service uom in row {row_num_in_sheet}. Skipping this row's order lines.")
                return []

            # Use this line in future for VAS details to be included in OriginalOrderLineRequestedServices for now it is mentioned as empty list []
            vas_detail = []
            sequence_nbr = 1

            def has_text_value(value):
                if value is None:
                    return False
                if isinstance(value, str):
                    return value.strip() != ''
                return True

            for instruction_code_id, instruction_text_id in zip(current_instruction_code_id, current_instruction_text_id):
                has_formatted_dlvd = has_text_value(formatted_dlvd)
                if instruction_code_id == 'ZIDP' and not has_formatted_dlvd:
                    continue

                instr_text_3 = ''
                if instruction_code_id in ('LBL', 'CST', 'PRI', 'COI'):
                    instr_text_3 = instruction_text_id
                else:
                    instr_text_3 = ''

                instr_text_1 = ''
                if instruction_code_id == 'PUP':
                    instr_text_1 = instruction_text_id
                elif instruction_code_id == 'ZIDP':
                    instr_text_1 = formatted_dlvd
                else:
                    instr_text_1 = ''

                if instruction_code_id in ('BOX', 'CTL', 'COI') and instruction_text_id == '0':
                    instr_text_1 = None
                    instr_text_3 = None


                skip_instruction_text_1_2 = instruction_code_id in ('BOX', 'CTL', 'COI')
                fulfillmentrequest_item_instruction = {
                    "instructionCode": instruction_code_id,
                    "instructionTypeCode": instruction_code_type,
                    "vasIndicator": True
                }

                if not skip_instruction_text_1_2:
                    if has_text_value(instr_text_1):
                        fulfillmentrequest_item_instruction["instruction1Text"] = instr_text_1
                    instruction2_text = "JPY"
                    if has_text_value(instruction2_text):
                        fulfillmentrequest_item_instruction["instruction2Text"] = instruction2_text

                if order_type != 'Z033':
                    if has_text_value(instr_text_3):
                        fulfillmentrequest_item_instruction["instruction3Text"] = instr_text_3

                vas_detail.append(fulfillmentrequest_item_instruction)
                sequence_nbr += 1

            nondigital_extra_fulfillmentrequest_item_instruction = [
                {"instructionCode": "0001", "instruction1Text": "ｾｲﾙ/ｲｴﾛｰｵｰｶｰ/ｺﾞﾙｼﾞｭｸﾞﾘｰﾝ", "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ｾｲﾙ/ｲｴﾛｰｵｰｶｰ/", "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ﾅｲｷ ｺｰﾄ ﾎﾞﾛｰ LOW PREM", "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ﾅｲｷ ｺｰﾄ ﾎﾞﾛｰ", "vasIndicator": False}
                ]
            if has_text_value(formatted_dlvd):
                nondigital_extra_fulfillmentrequest_item_instruction.append(
                    {"instructionCode": "ZIDP", "instruction1Text": formatted_dlvd, "vasIndicator": False}
                )

            digital_extra_fulfillmentrequest_item_instruction = [
                {"instruction1Text": "ﾌﾞﾗｯｸ", "instructionCode": "0001", "vasIndicator": False},
                {"instruction1Text": "ﾌﾞﾗｯｸ", "instructionCode": "0001", "vasIndicator": False},
                {"instruction1Text": "ｳｨﾒﾝｽﾞ ｼﾞｮｰﾀﾞﾝ SPT ﾀﾞｲﾔﾓﾝﾄﾞ ﾀﾝｸﾄｯﾌﾟ", "instructionCode": "0001", "vasIndicator": False},
                {"instruction1Text": "ｳｨﾒﾝｽﾞ ｼﾞｮｰﾀ", "instructionCode": "0001", "vasIndicator": False}
            ]

            if order_type == 'Z033':
                for entry in digital_extra_fulfillmentrequest_item_instruction:
                    vas_detail.append(entry)
            else:
                for entry in nondigital_extra_fulfillmentrequest_item_instruction:
                    vas_detail.append(entry)

            # Merge vas_detail directly into fulfillment_request_Item
            fulfillment_request_Item["fulfillmentRequestItemInstruction"] = vas_detail

            order_line_list.append(fulfillment_request_Item)
            order_line_id += 1

        return order_line_list

    @property
    def generate_payloads(self) -> list[Any]:
        global current_order_id
        try:
            list_of_datadict = self.worksheet.create_fr_order_extract_parameters()
            if list_of_datadict is None:
                logging.error("Error: Outbound Worksheet Extract method returned None. Halting generation.")
                return []  # Return empty list on failure
        except Exception as e:
            logging.error(f"Error: {e}")
            return []

        logging.info(f"Successfully extracted {len(list_of_datadict)} data row(s) for processing.")

        # Helper function to convert ASCII characters to full-width
        def to_full_width(text):
            if not isinstance(text, str):
                return text  # Return as is if not a string

            full_width_chars = []
            for char in text:
                # Convert ASCII digits to full-width
                if '0' <= char <= '9':
                    full_width_chars.append(chr(ord(char) - ord('0') + 0xFF10))
                # Convert ASCII uppercase letters to full-width (for AM/PM)
                elif 'A' <= char <= 'Z':
                    full_width_chars.append(chr(ord(char) - ord('A') + 0xFF21))
                # Convert common symbols to full-width
                elif char == '/':
                    full_width_chars.append('／')
                elif char == ':':
                    full_width_chars.append('：')
                else:
                    full_width_chars.append(char)
            return "".join(full_width_chars)

        self.all_order_payloads = []

        for i, data_row in enumerate(list_of_datadict):
            row_num_in_sheet = i + 1
            logging.info(f"Processing Excel Row {row_num_in_sheet}")

            plant = str(data_row.get("plant"))
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
            address_2 = data_row.get("address_2")
            street_address_1 = data_row.get("street_address1")
            street_address_2 = data_row.get("street_address2")
            item = data_row.get("item")
            gtin = data_row.get('gtin')
            qty = str(data_row.get("qty"))
            d_facility = data_row.get("d_facility")
            pre_pack_code = data_row.get("pre_pack_code")
            instruction_code = data_row.get("instruction_code", 'BOX')
            instruction_text = data_row.get("instruction_text", 'oLPN')
            carrier_code = data_row.get("carrier_code")
            hub_code = data_row.get("hub_code")
            sub_hub = data_row.get("sub_hub")
            route_number_raw = data_row.get("route_number")
            # Default to empty string if None or NaN
            route_number = '' if (route_number_raw is None or pd.isna(route_number_raw)) else str(route_number_raw)
            mark_for_customer_id_raw = data_row.get("mark_for_customer_id")
            # Default to empty string if None or NaN
            mark_for_customer_id = '' if (
                        mark_for_customer_id_raw is None or pd.isna(mark_for_customer_id_raw)) else str(
                mark_for_customer_id_raw)
            sold_to_facility_id = data_row.get("sold_to_facility_id")
            pickup_dttm = datetime.strptime(str(data_row.get("pickup_dttm")), "%m/%d/%Y")
            delivery_dttm = datetime.strptime(data_row.get("delivery_dttm"), "%m/%d/%Y")
            dlvd = data_row.get("dlvd")

            order_ids = self.number_gen.fr_order_number_generation(num_of_order, envn, user_initial)

            if not order_ids:
                logging.error(f"INFO: Skipping row {row_num_in_sheet} as 'Number of Orders' is 0 or invalid entry is given")
                continue

            for order_index, current_order_id in enumerate(order_ids):
                logging.info(f"Order: {current_order_id}")

            party_identifier = ''
            customer_po_type = ''
            instr_code = ''
            consumer_sales_order_number = ''
            if order_type == "Z033":
                party_identifier = 'Digital'
                customer_po_type = 'DTCJ'
                instr_code = 'ZGFR'
                consumer_sales_order_number = self.po_nbr
            else:
                party_identifier = 'WHOLE_SALE_DC'
                customer_po_type = ''
                instr_code = 'ZGRS'
                consumer_sales_order_number = ''


            formatted_pickup_dttm = pickup_dttm.strftime("%m%d%y 05:01")
            formatted_delivery_dttm = delivery_dttm.strftime("%m%d%y 12:59")
            formatted_dlvd = to_full_width(str(dlvd)) if dlvd and not pd.isna(dlvd) else ""
            now = datetime.today().strftime("%Y-%m-%d")
            formatted_now = f"{now}T00:00:00"
            change_format_pickup_dttm = pickup_dttm.strftime("%Y-%m-%d")
            change_format_delivery_dttm = delivery_dttm.strftime("%Y-%m-%d")
            fr_request_pickup_date = pickup_dttm.strftime("%Y-%m-%dT00:00:00")
            fr_request_delivery_date = delivery_dttm.strftime("%Y-%m-%dT00:00:00")


            nondigital_fulfillment_request_party = [
                    {
                        "partyTypeCode": "SOLD_TO", "partyIdentifierType": party_identifier,
                        "partyIdentifier": f"{sold_to_facility_id}", "partyName1": first_name,
                        "fulfillmentRequestLocationAddress": {
                            "addressLine1Text": address_1, "cityName": city, "stateProvinceCode": state,
                            "postalCode": postal_code, "countryCode": country, "languageCode": "JA",
                            "addressLine2Text": address_2, "streetAddress1": street_address_1,
                            "streetAddress2": street_address_2
                        },
                        "fulfillmentRequestContact": {"dayPhoneNumber": phone}
                    },
                    {
                        "partyTypeCode": "CARRIER", "partyIdentifierType": party_identifier,
                        "partyIdentifier": f"{carrier_code}",
                        "fulfillmentRequestLocationAddress": {
                            "transportationZone": f"{hub_code}", "transportationSubZone": f"{sub_hub}"
                        }
                    },
                    {
                        "partyTypeCode": "SHIP_TO", "partyIdentifierType": party_identifier,
                        "partyIdentifier": f"{d_facility}", "partyName1": first_name,
                        "fulfillmentRequestLocationAddress": {
                            "addressLine1Text": address_1, "cityName": city, "stateProvinceCode": state,
                            "postalCode": postal_code, "countryCode": country,  "languageCode": "JA",
                            "addressLine2Text": address_2, "streetAddress1": street_address_1,
                            "streetAddress2": street_address_2
                        },
                        "fulfillmentRequestContact": {"dayPhoneNumber": phone}
                    },
                    {
                        "partyTypeCode": "SHIP_FROM", "partyIdentifierType": party_identifier, "partyIdentifier": f"{plant}"
                    }
                ]


            digital_fulfillment_request_party = [
                {
                    "fulfillmentRequestContact": {"dayPhoneNumber": phone},
                    "fulfillmentRequestLocationAddress": {
                        "addressLine1Text": address_1, "addressLine2Text": address_2, "cityName": city,
                        "countryCode": country, "languageCode": "JA", "postalCode": postal_code, "stateProvinceCode": state,
                        "streetAddress1": street_address_1, "streetAddress2": street_address_2
                    },
                    "partyIdentifierType": party_identifier, "partyIdentifier": f"{sold_to_facility_id}",
                    "partyName1": first_name, "partyTypeCode": "SOLD_TO",
                },
                {
                    "partyTypeCode": "CARRIER", "partyIdentifierType": party_identifier,
                    "partyIdentifier": f"{carrier_code}",
                    "fulfillmentRequestLocationAddress": {
                        "transportationZone": f"{hub_code}", "transportationSubZone": f"{sub_hub}"
                    }
                },
                {
                    "fulfillmentRequestContact": {"dayPhoneNumber": phone, "emailAddressText": "testdata@nike.com"},
                    "fulfillmentRequestLocationAddress": {
                        "addressLine1Text": address_1, "addressLine2Text": address_2, "cityName": city,
                        "countryCode": country, "languageCode": "JA", "postalCode": postal_code, "stateProvinceCode": state,
                        "streetAddress1": street_address_1, "streetAddress2": street_address_2
                    },
                    "partyIdentifier": f"{d_facility}", "partyIdentifierType": party_identifier,
                    "partyName1": first_name, "partyName2": "Fabron Boscawen", "partyTypeCode": "SHIP_TO"
                },
                {
                    "partyIdentifier": f"{plant}", "partyIdentifierType": party_identifier, "partyTypeCode": "SHIP_FROM"
                },
                {
                    "fulfillmentRequestContact": {"dayPhoneNumber": phone},
                    "fulfillmentRequestLocationAddress": {
                        "addressLine1Text": address_1, "addressLine2Text": address_2, "cityName": city,
                        "countryCode": country, "languageCode": "JA", "postalCode": postal_code, "stateProvinceCode": state,
                        "streetAddress1": street_address_1, "streetAddress2": street_address_2
                    },
                    "partyIdentifier": f"{d_facility}", "partyIdentifierType": party_identifier,
                    "partyName1": first_name, "partyName2": "Fabron Boscawen", "partyTypeCode": "BILL_TO"
                }
            ]
            nondigital_fulfillment_Request_Instruction = [
                {"instructionCode": instr_code, "instruction1Text": formatted_pickup_dttm, "vasIndicator": False},
                {"instructionCode": "ZGRE", "instruction1Text": formatted_delivery_dttm, "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ｾｲﾙ/ｲｴﾛｰｵｰｶｰ/ｺﾞﾙｼﾞｭｸﾞﾘｰﾝ", "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ｾｲﾙ/ｲｴﾛｰｵｰｶｰ/", "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ﾅｲｷ ｺｰﾄ ﾎﾞﾛｰ LOW PREM", "vasIndicator": False},
                {"instructionCode": "0001", "instruction1Text": "ﾅｲｷ ｺｰﾄ ﾎﾞﾛｰ", "vasIndicator": False}
            ]
            if isinstance(formatted_dlvd, str) and formatted_dlvd.strip():
                nondigital_fulfillment_Request_Instruction.append(
                    {"instructionCode": "ZIDP", "instruction1Text": formatted_dlvd, "vasIndicator": False}
                )

            digital_fulfillment_Request_Instruction = [
                {"instructionCode": 'ZGFR', "instruction1Text": 'N', "vasIndicator": False},
                {"instructionCode": "ZPMT", "instruction1Text": 'Visa0001', "vasIndicator": False},
                {"instruction1Text": "ﾌﾞﾗｯｸ", "instructionCode": "0001", "vasIndicator": False},
                {"instruction1Text": "ﾌﾞﾗｯｸ", "instructionCode": "0001", "vasIndicator": False},
                {"instruction1Text": "ｳｨﾒﾝｽﾞ ｼﾞｮｰﾀﾞﾝ SPT ﾀﾞｲﾔﾓﾝﾄﾞ ﾀﾝｸﾄｯﾌﾟ", "instructionCode": "0001", "vasIndicator": False},
                {"instruction1Text": "ｳｨﾒﾝｽﾞ ｼﾞｮｰﾀ", "instructionCode": "0001", "vasIndicator": False}
            ]

            digital_fulfillment_request_date = {
                "cancelByDt": change_format_pickup_dttm, "plannedPickingTimestamp": fr_request_pickup_date,
                "plannedGoodsIssueTimestamp": fr_request_pickup_date, "estimatedDeliveryTimestamp": fr_request_delivery_date,
                "fulfillmentRequestCreateTimestamp": formatted_now, "customerRequestTimestamp": fr_request_delivery_date,
                "customerOrderCreateTimestamp": formatted_now,
            }

            nondigital_fulfillment_request_date  = {
                "cancelByDt": change_format_pickup_dttm, "plannedPickingTimestamp": fr_request_pickup_date,
                "plannedGoodsIssueTimestamp": fr_request_pickup_date, "estimatedDeliveryTimestamp": fr_request_delivery_date,
                "fulfillmentRequestCreateTimestamp": formatted_now, "customerRequestTimestamp": fr_request_delivery_date,
                "deliveryPlanScheduledDeliveryDate": change_format_delivery_dttm, "deliveryPlanScheduledProcessingDate": change_format_pickup_dttm,
                "customerOrderCreateTimestamp": formatted_now, "scheduledDeliveryStartTimestamp": fr_request_delivery_date
            }

            fulfillment_request_reference = [
                {"referenceNumberTypeCode": "SALES_DOCUMENT_NUMBER", "referenceNumberValue": "0328139201"},
                {"referenceNumberTypeCode": "CONSUMER_SALES_ORDER_NUMBER", "referenceNumberValue": 'KT8178021221'},
                {"referenceNumberTypeCode": "INITIATING_DOCUMENT_NUMBER", "referenceNumberValue": self.po_nbr}
            ]

            order_line_info: list = self._parse_order_line_item(item, qty, instruction_code, instruction_text, order_type,
                                                          row_num_in_sheet, plant, gtin, formatted_dlvd, fr_request_delivery_date)


            fulfillmentrequestheader = {
                "event": {"timestamp": formatted_now},
                "fulfillmentRequestHeader": {
                    "fulfillmentRequestNumber": current_order_id, "orderGroupType": "ZLF", "orderType": order_type,
                    "fulfillmentRequestType": "ZLF", "shippingPointCode": plant, "routeNumber": route_number,
                    "salesOrganizationCode": "7000", "incoTermsCode": "DDP", "exportIndicator": False,
                    "shipToAddressOverrideIndicator": False, "customerDocumentRequiredIndicator": False,
                    "customerPOType": customer_po_type, "serviceLevelCode": service_level,
                    "appointmentSchedulingIndicator": True, "currencyCode": "JPY", "consumerRequestedMethod": "SHIP",
                    "fulfillmentMethod": "SHIP", "immediateReleaseIndicator": False, "salesDeliveryPriority": "02",
                    "directOrderDropIndicator": False, "vendorNumber": "NIKE",
                    "fulfillmentRequestReference": fulfillment_request_reference,
                    "fulfillmentRequestDate": nondigital_fulfillment_request_date if order_type != 'Z033' else digital_fulfillment_request_date,
                    "fulfillmentRequestItem": order_line_info,
                    "fulfillmentRequestParty": nondigital_fulfillment_request_party if order_type != 'Z033' else digital_fulfillment_request_party,
                    "fulfillmentRequestInstruction": nondigital_fulfillment_Request_Instruction if order_type != "Z033" else digital_fulfillment_Request_Instruction
                }
            }

            self.all_order_payloads.append(fulfillmentrequestheader)

        return self.all_order_payloads

if __name__ == "__main__":
    fr_order_generation = FR_Order_Creation_Payload()
    final_payloads = fr_order_generation.generate_payloads
    # Optional: Pretty-print the first payload for verification
    if final_payloads:
        import json
        for i, payloads in enumerate(final_payloads):
            num = i+1
            logging.info(f"No {num} Generated Payload")
            print(json.dumps(payloads, indent=2, ensure_ascii=False))