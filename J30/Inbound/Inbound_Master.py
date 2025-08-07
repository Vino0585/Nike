import logging
import pandas as pd
import time

from Payload_generation.Worksheet_extract import Worksheet
from ASN_Creation import ASN_Creation
from Inbound_Delivery import Inbound_Delivery
from Good_Holder_Announced import Goods_Holder_Announced
from Goods_Holder_Measured import Goods_Holder_Measured
from Putaway_Complete import Putaway_Complete
from ASN_Verify import ASN_Verify
from MHE_Jounal_IB import MHE_Journal_Inbound


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
            asn_verify = entry.get("ASNVerify")
            run_all = entry.get("RunAll", 'N')

            if (create_asn == 'Y' and self.is_no_or_empty(inbound_delivery)
                and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                logging.info("ASN Creation Program Started Successfully")
                asn_create = ASN_Creation()
                asn_create.create_asns()
                logging.info("ASN Created Program Completed Successfully")

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and self.is_no_or_empty(goods_holder_announced) and
                  self.is_no_or_empty(goods_holder_weighed) and self.is_no_or_empty(putaway_complete) and
                  self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                logging.info("ASN Creation Program Started Successfully")
                asn_create = ASN_Creation()
                asn_create.create_asns()
                logging.info("ASN Created Program Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the inbound delivery function
                print("\n")
                logging.info(f"Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                logging.info("ASN Creation Program Started Successfully")
                asn_create = ASN_Creation()
                asn_create.create_asns()
                logging.info("ASN Created Program Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                logging.info("Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                logging.info("Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")

                time.sleep(40)

                print("\n")
                logging.info("Message Journal Program Started Successfully")
                mhe_journal_inbound = MHE_Journal_Inbound()
                mhe_journal_inbound.create_mhe_journal_inbound()
                logging.info("Message Journal Program Completed Successfully")

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y'
                  and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                logging.info("ASN Creation Program Started Successfully")
                asn_create = ASN_Creation()
                asn_create.create_asns()
                logging.info("ASN Created Program Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                logging.info("Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                logging.info("Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()

                time.sleep(35)

                print("\n")
                logging.info("Message Journal Program Started Successfully")
                mhe_journal_inbound = MHE_Journal_Inbound()
                mhe_journal_inbound.create_mhe_journal_inbound()
                logging.info("Message Journal Program Completed Successfully")

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y' and
                    putaway_complete == 'Y' and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                logging.info(f"ASN Creation Program Started Successfully")
                asn_create = ASN_Creation()
                asn_create.create_asns()
                logging.info("ASN Created Program Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                logging.info(f"Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                logging.info(f"Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                logging.info("Goods Holder Measured Program Started Successfully")
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()
                logging.info("Goods Holder Measured Program Completed Successfully")

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")

                time.sleep(30)

                print("\n")
                logging.info("Message Journal Program Started Successfully")
                mhe_journal_inbound = MHE_Journal_Inbound()
                mhe_journal_inbound.create_mhe_journal_inbound()
                logging.info("Message Journal Program Completed Successfully")

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y' and
                    putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the inbound delivery function
                logging.info("Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the goods holder announced function
                logging.info("Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the goods holder measured function.
                logging.info("Goods Holder Measured Program Started Successfully")
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()
                logging.info("Goods Holder Measured Program Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")
                print("\n")
                time.sleep(30)

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y' and
                    putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the goods holder announced function
                logging.info("Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the goods holder measured function.
                logging.info("Goods Holder Measured Program Started Successfully")
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()
                logging.info("Goods Holder Measured Program Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")
                print("\n")
                time.sleep(30)

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and goods_holder_weighed == 'Y' and
                  putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the goods holder measured function.
                logging.info("Goods Holder Measured Program Started Successfully")
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()
                logging.info("Goods Holder Measured Program Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")
                print("\n")
                time.sleep(30)

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")
                print("\n")
                time.sleep(30)

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")
                print("\n")
                time.sleep(30)

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery)
                and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and run_all == 'Y'):

                # Calling the Create ASN function
                logging.info("ASN Creation Program Started Successfully")
                asn_create = ASN_Creation()
                asn_create.create_asns()
                logging.info("ASN Created Program Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the inbound delivery function
                logging.info("Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the goods holder announced function
                logging.info("Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the goods holder measured function.
                logging.info("Goods Holder Measured Program Started Successfully")
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()
                logging.info("Goods Holder Measured Program Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")
                print("\n")
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")
                print("\n")
                time.sleep(30)

                logging.info("Message Journal Program Started Successfully")
                mhe_journal_inbound = MHE_Journal_Inbound()
                mhe_journal_inbound.create_mhe_journal_inbound()
                logging.info("Message Journal Program Completed Successfully")
                print("\n")
                time.sleep(1)

                logging.info("Run All Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and inbound_delivery == 'Y' and
                  self.is_no_or_empty(goods_holder_announced) and  self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                logging.info(f"Inbound Delivery Program Started Successfully")
                ib_delivery = Inbound_Delivery()
                ib_delivery.send_inbound_delivery()
                logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  goods_holder_announced == 'Y' and  self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the goods holder announced function
                logging.info("Goods Holder Announced Program Started Successfully")
                gh_announced = Goods_Holder_Announced()
                gh_announced.send_goods_holder_announced()
                logging.info("Goods Holder Announced Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and  goods_holder_weighed == 'Y' and
                  self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the goods holder measured function.
                logging.info("Goods Holder Measured Program Started Successfully")
                gh_measured = Goods_Holder_Measured()
                gh_measured.send_goods_holder_measured()
                logging.info("Goods Holder Measured Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  putaway_complete == 'Y' and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the Putaway Complete Function.
                logging.info("Putaway Completed Program Started Successfully")
                ptwy_complete = Putaway_Complete()
                ptwy_complete.create_putaway_task_complete()
                logging.info("Putaway Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and asn_verify == 'Y' and
                  self.is_no_or_empty(run_all)):

                # Calling the ASN Verification Function
                logging.info("ASN Verification Started Successfully")
                asn_verify = ASN_Verify()
                asn_verify.send_asn_verify()
                logging.info("ASN Verified Successfully")

            else:
                logging.info(f"The combination provided doesnt match the requirement "
                             f"therefore the program didnt produce any output.")

inbound_master = inbound_master_step()
inbound_master.get_inbound_master_worksheet_extract()