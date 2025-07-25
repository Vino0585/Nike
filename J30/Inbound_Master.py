import logging
import pandas as pd
from Payload_generation.Worksheet_extract import Worksheet
from ASN_Creation import ASN_Creation


class inbound_master_step:

    def is_no_or_empty(self, value):
        return value == 'N' or pd.isna(value) or value is None

    def get_inbound_master_worksheet_extract(self):
        worksheet = Worksheet()
        get_entry = worksheet.extract_master_sheet_from_worksheet()

        if not get_entry:
            logging.error("The worksheet returned nothing check worksheet program extract_master_sheet_from_worksheet function.")
            return None

        for entry in get_entry:
            create_asn = entry.get("CreateASN", 'Y')
            inbound_delivery = entry.get("InboundDelivery")
            goods_holder_announced = entry.get("GH_Announced")
            goods_holder_weighed = entry.get("GH_Weighed")
            putaway_complete = entry.get("PutawayComplete")
            run_all = entry.get("RunAll", 'N')

            if (create_asn == 'Y' and self.is_no_or_empty(inbound_delivery)
                and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(run_all)):

                asn_create = ASN_Creation()
                asn_create.create_asns()

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(run_all)):

                asn_create = ASN_Creation()
                asn_create.create_asns()



