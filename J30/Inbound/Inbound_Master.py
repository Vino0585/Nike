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

    def __init__(self):
        """Initialize all service classes once to be reused."""
        self.worksheet_extractor = Worksheet()
        self.asn_creation = ASN_Creation()
        self.inbound_delivery = Inbound_Delivery()
        self.goods_holder_announced = Goods_Holder_Announced()
        self.goods_holder_measured = Goods_Holder_Measured()
        self.putaway_complete = Putaway_Complete()
        self.asn_verify = ASN_Verify()
        self.mhe_journal_inbound = MHE_Journal_Inbound()

    def is_no_or_empty(self, value):
        return value == 'N' or pd.isna(value) or value is None

    def call_asn_creation_program(self):
        # Calling the Create ASN function
        logging.info("ASN Creation Program Started Successfully")
        self.asn_creation.create_asns()
        logging.info("ASN Created Program Completed Successfully")

    def call_inbound_delivery_program(self):
        # Calling the inbound delivery function
        logging.info("Inbound Delivery Program Started Successfully")
        self.inbound_delivery.send_inbound_delivery()
        logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")

    def call_goods_holder_announced_program(self):
        # Calling the goods holder announced function
        logging.info("Goods Holder Announced Program Started Successfully")
        self.goods_holder_announced.send_goods_holder_announced()
        logging.info("Goods Holder Announced Completed Successfully")

    def call_goods_holder_measured_program(self):
        # Calling the goods holder measured function.
        logging.info("Goods Holder Measured Program Started Successfully")
        self.goods_holder_measured.send_goods_holder_measured()
        logging.info("Goods Holder Measured Program Completed Successfully")

    def call_putaway_complete_program(self):
        # Calling the Putaway Complete Function.
        logging.info("Putaway Completed Program Started Successfully")
        self.putaway_complete.create_putaway_task_complete()
        logging.info("Putaway Completed Successfully")

    def call_asn_verify_program(self):
        # Calling the ASN Verification Function
        logging.info("ASN Verification Started Successfully")
        self.asn_verify.send_asn_verify()
        logging.info("ASN Verified Successfully")

    def call_mhe_journal_inbound_program(self):
        # Calling the Message Journal Program
        logging.info("Message Journal Program Started Successfully")
        self.mhe_journal_inbound.create_mhe_journal_inbound()
        logging.info("Message Journal Program Completed Successfully")

    def get_inbound_master_worksheet_extract(self):
        get_entry = self.worksheet_extractor.extract_master_sheet_from_worksheet()

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

                self.call_asn_creation_program()
                logging.info("Program Completed Successfully")
                print("\n")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and self.is_no_or_empty(goods_holder_announced) and
                  self.is_no_or_empty(goods_holder_weighed) and self.is_no_or_empty(putaway_complete) and
                  self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                self.call_asn_creation_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                self.call_asn_creation_program()
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()
                time.sleep(40)
                print("\n")

                self.call_mhe_journal_inbound_program()
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y'
                  and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                self.call_asn_creation_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()

                time.sleep(35)

                print("\n")
                self.call_mhe_journal_inbound_program()

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y' and
                    putaway_complete == 'Y' and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):

                # Calling the Create ASN function
                self.call_asn_creation_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()

                time.sleep(30)

                print("\n")
                self.call_mhe_journal_inbound_program()

                time.sleep(1)
                print("\n")
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and 
                  goods_holder_weighed == 'Y' and putaway_complete == 'Y' and asn_verify == 'Y' and 
                  self.is_no_or_empty(run_all)):

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()
                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the ASN Verification Function
                self.call_asn_verify_program()
                print("\n")
                time.sleep(30)

                self.call_mhe_journal_inbound_program()
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and goods_holder_announced == 'Y'
                  and goods_holder_weighed == 'Y' and
                    putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the ASN Verification Function
                self.call_asn_verify_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(30)
                print("\n")

                self.call_mhe_journal_inbound_program()
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and goods_holder_weighed == 'Y' and
                  putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the ASN Verification Function
                self.call_asn_verify_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(30)
                print("\n")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the ASN Verification Function
                self.call_asn_verify_program()

                # Deliberately creating delay of 30 seconds for each function execution
                time.sleep(30)
                print("\n")

                # Calling the MHE journal program
                self.call_mhe_journal_inbound_program()

                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and asn_verify == 'Y' and self.is_no_or_empty(run_all)):

                # Calling the ASN Verification Function
                self.call_asn_verify_program()

                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery)
                and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
                and self.is_no_or_empty(putaway_complete) and run_all == 'Y'):

                # Calling the Create ASN function
                self.call_asn_creation_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(5)
                print("\n")

                # Calling the ASN Verification Function
                self.call_asn_verify_program()

                # Deliberately creating delay of 5 seconds for each function execution
                time.sleep(30)
                print("\n")

                # Calling the MHE Journal function.
                self.call_mhe_journal_inbound_program()

                print("\n")
                logging.info("Run All Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and inbound_delivery == 'Y' and
                  self.is_no_or_empty(goods_holder_announced) and  self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the inbound delivery function
                self.call_inbound_delivery_program()
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  goods_holder_announced == 'Y' and  self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the goods holder announced function
                self.call_goods_holder_announced_program()
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and  goods_holder_weighed == 'Y' and
                  self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the goods holder measured function.
                self.call_goods_holder_measured_program()
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  putaway_complete == 'Y' and self.is_no_or_empty(asn_verify) and
                  self.is_no_or_empty(run_all)):

                # Calling the Putaway Complete Function.
                self.call_putaway_complete_program()
                logging.info("Program Completed Successfully")

            elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
                  self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
                  self.is_no_or_empty(putaway_complete) and asn_verify == 'Y' and
                  self.is_no_or_empty(run_all)):

                # Calling the ASN Verification Function
                self.call_asn_verify_program()
                logging.info("Program Completed Successfully")

            else:
                logging.info(f"The combination provided doesnt match the requirement "
                             f"therefore the program didnt produce any output.")

inbound_master = inbound_master_step()
inbound_master.get_inbound_master_worksheet_extract()