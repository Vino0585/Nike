from Payload_generation.Worksheet_extract import Worksheet
import logging

# Setup basic logging to provide better feedback than print()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ASN_Search_Payload:
    def __init__(self):
        self.worksheet = Worksheet()
        self.all_asn_search_worksheet_parameter = self.worksheet.search_asn_extract_parameters()
        self.inbound_delivery_worksheet_extract = self.worksheet.inbound_delivery_worksheet_extract()
        self.all_asn_search_payload = []


    def parse_asn_search_worksheet(self) -> list:
        if not self.all_asn_search_worksheet_parameter:
            logging.error("No valid ASN parameters found in the worksheet.")
            return None

        for entry in self.all_asn_search_worksheet_parameter:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id_str = entry.get("ASNID")

            if not (asn_id_str and isinstance(asn_id_str, str)):
                logging.info(f"--> WARNING: Skipping row for Plant {plant} due to invalid or empty ASNID.")
                continue

            # Cleanly split, strip whitespace, and filter out any empty strings
            cleaned_asn_ids = [item.strip() for item in asn_id_str.split(';') if item.strip()]

            if not cleaned_asn_ids:
                logging.info(f"--> WARNING: Skipping row for Plant {plant} as no valid ASN IDs were found after cleaning.")
                continue


            self.all_asn_search_payload.append({
                                                "plant": str(plant),
                                                "environment": envn,
                                                "asn_ids": cleaned_asn_ids  # Store as a list for easier processing later
                                                })
        return self.all_asn_search_payload

    def parse_asn_response(self, response_data: dict) -> list:
        """
        Parses the ASN API response and extracts key fields into a list of dictionaries.
        This function no longer writes to a file; it just returns the data.
        """
        if not response_data.get("data"):
            logging.error("-> Success, but no ASN data was returned in the response.")
            return []

        extracted_rows = []
        for asn in response_data.get("data", []):
            for lpn in asn.get("Lpn", []):
                for detail in lpn.get("LpnDetail", []):
                    if asn.get("ShipmentAsnAssociation"):
                        row = {
                            "AsnId": asn.get("AsnId"),
                            "AsnStatus": asn.get("AsnStatus"),
                            "AsnOriginTypeId": asn.get("AsnOriginTypeId"),
                            "InboundDelivery": (asn.get("ShipmentAsnAssociation")[0]["ShipmentId"], 0),
                            "Expedited_Flag": asn.get("Extended").get("ExpeditedFlag"),
                            "LpnId": lpn.get("LpnId"),
                            "LpnStatus": lpn.get("LpnStatus"),
                            "ItemId": detail.get("ItemId"),
                            "ShippedQty": detail.get("ShippedQuantity"),
                            "DiversionCode": lpn.get('DiversionCodeId'),
                            "Pre_receipt_Status": asn.get("PreReceiptStatusId"),
                            "Single_Item_LPN": lpn.get("SingleItemLpn"),
                            "BOL": asn.get('BillOfLadingNumber'),
                            "ProNbr": asn.get('ProNumber'),
                            "Carrier": asn.get('CarrierId'),
                            "LPNSizeType": lpn.get('LpnSizeTypeId'),
                            "Length": lpn['Extended'].get('LpnLength'),
                            "Height": lpn['Extended'].get('LpnHeight'),
                            "Width": lpn['Extended'].get('LpnWidth'),
                            "Origin_facility": asn.get('OriginFacilityId'),
                            "TrailerNbr": asn.get('TrailerId'),
                            "UpdatedBy": detail.get("UpdatedBy"),
                            "UpdatedTimestamp": detail.get("UpdatedTimestamp")
                        }
                        extracted_rows.append(row)
                    else:
                        row = {
                            "AsnId": asn.get("AsnId"),
                            "AsnStatus": asn.get("AsnStatus"),
                            "AsnOriginTypeId": asn.get("AsnOriginTypeId"),
                            "Expedited_Flag": asn.get("Extended").get("ExpeditedFlag"),
                            "LpnId": lpn.get("LpnId"),
                            "LpnStatus": lpn.get("LpnStatus"),
                            "ItemId": detail.get("ItemId"),
                            "ShippedQty": detail.get("ShippedQuantity"),
                            "DiversionCode": lpn.get('DiversionCodeId'),
                            "Pre_receipt_Status": asn.get("PreReceiptStatusId"),
                            "Single_Item_LPN": lpn.get("SingleItemLpn"),
                            "BOL": asn.get('BillOfLadingNumber'),
                            "ProNbr": asn.get('ProNumber'),
                            "Carrier": asn.get('CarrierId'),
                            "LPNSizeType": lpn.get('LpnSizeTypeId'),
                            "Length": lpn['Extended'].get('LpnLength'),
                            "Height": lpn['Extended'].get('LpnHeight'),
                            "Width": lpn['Extended'].get('LpnWidth'),
                            "Origin_facility": asn.get('OriginFacilityId'),
                            "TrailerNbr": asn.get('TrailerId'),
                            "UpdatedBy": detail.get("UpdatedBy"),
                            "UpdatedTimestamp": detail.get("UpdatedTimestamp")
                        }
                        extracted_rows.append(row)
        return extracted_rows


    def parse_asn_inbound_delivery_search_worksheet(self) -> list:
        if not self.inbound_delivery_worksheet_extract:
            logging.error("No valid ASN parameters found in the worksheet.")
            return None

        for entry in self.all_asn_search_worksheet_parameter:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            asn_id_str = entry.get("ASNID")

            if not (asn_id_str and isinstance(asn_id_str, str)):
                logging.info(f"--> WARNING: Skipping row for Plant {plant} due to invalid or empty ASNID.")
                continue

            # Cleanly split, strip whitespace, and filter out any empty strings
            cleaned_asn_ids = [item.strip() for item in asn_id_str.split(';') if item.strip()]

            if not cleaned_asn_ids:
                logging.info(f"--> WARNING: Skipping row for Plant {plant} as no valid ASN IDs were found after cleaning.")
                continue


            self.all_asn_search_payload.append({
                                                "plant": str(plant),
                                                "environment": envn,
                                                "asn_ids": cleaned_asn_ids  # Store as a list for easier processing later
                                                })
        return self.all_asn_search_payload

    def parse_asn_inbound_delivery_response(self, response_data: dict) -> list:
        if not response_data.get("data"):
            logging.error("-> Success, but no ASN data was returned in the response.")
            return []

        shipment_id = []
        for asn in response_data.get("data", []):
            ship_id = asn.get("ShipmentAsnAssociation")[0]["ShipmentId"]
            shipment_id.append(ship_id)

        return shipment_id

# initiate = ASN_Search_Payload()
# result = initiate.parse_asn_response()
# print(result)