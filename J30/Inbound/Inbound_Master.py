import logging
import pandas as pd
import time

from Inbound.Payload_generation.Worksheet_extract import Worksheet
from ASN_Creation import ASN_Creation
from Inbound_Delivery import Inbound_Delivery
# from iLPN_Information import iLPN_Information
# from Routing_Task_Completed import Routing_Task_Completed
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
        # self.iLPN_information = iLPN_Information()
        # self.routing_task_completed = Routing_Task_Completed()
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
        print("\n")
        time.sleep(5)

    def call_inbound_delivery_program(self):
        # Calling the inbound delivery function
        logging.info("Inbound Delivery Program Started Successfully")
        self.inbound_delivery.send_inbound_delivery()
        logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")
        print("\n")
        time.sleep(5)

    # def call_exception_flow(self):
    #     logging.info("Exception Flow Started")
    #     logging.info("Filling iLPN Information for Routing Task Completed")
    #     self.iLPN_information.search_lpn_information()
    #     logging.info("Completed iLPN Information filling")
    #     logging.info("Starting Routing Task Complete Flow")
    #     self.routing_task_completed.create_routing_task_complete()
    #     logging.info("Routing Task Complete Flow Completed")
    #     logging.info("Exception Flow Completed")

    def call_goods_holder_announced_program(self):
        # Calling the goods holder announced function
        logging.info("Goods Holder Announced Program Started Successfully")
        self.goods_holder_announced.send_goods_holder_announced()
        logging.info("Goods Holder Announced Completed Successfully")
        print("\n")
        time.sleep(5)

    def call_goods_holder_measured_program(self):
        # Calling the goods holder measured function.
        logging.info("Goods Holder Measured Program Started Successfully")
        self.goods_holder_measured.send_goods_holder_measured()
        logging.info("Goods Holder Measured Program Completed Successfully")
        print("\n")
        time.sleep(5)

    def call_putaway_complete_program(self):
        # Calling the Putaway Complete Function.
        logging.info("Putaway Completed Program Started Successfully")
        self.putaway_complete.create_putaway_task_complete()
        logging.info("Putaway Completed Successfully")
        print("\n")
        time.sleep(5)

    def call_asn_verify_program(self):
        # Calling the ASN Verification Function
        logging.info("ASN Verification Started Successfully")
        self.asn_verify.send_asn_verify()
        logging.info("ASN Verified Successfully")
        print("\n")
        time.sleep(5)

    def call_mhe_journal_inbound_program(self):
        # Calling the Message Journal Program
        logging.info("Message Journal Program Started Successfully")
        self.mhe_journal_inbound.create_mhe_journal_inbound()
        logging.info("Message Journal Program Completed Successfully")

    def get_inbound_master_worksheet_extract(self):
        """Orchestrates the inbound process based on flags from a worksheet."""
        worksheet_entries = self.worksheet_extractor.extract_master_sheet_from_worksheet()

        if not worksheet_entries:
            logging.error("The worksheet returned no entries. Check the worksheet extraction program.")
            return

        # Define the sequence of operations, their flags, and associated logic
        operations = [
            {'flag': 'CreateASN', 'method': self.call_asn_creation_program},
            {'flag': 'InboundDelivery', 'method': self.call_inbound_delivery_program},
            # {'flag': 'ExceptionFlow', 'method': self.call_exception_flow, 'mhe_delay': 35},
            {'flag': 'GH_Announced', 'method': self.call_goods_holder_announced_program, 'mhe_delay': 60},
            {'flag': 'GH_Weighed', 'method': self.call_goods_holder_measured_program, 'mhe_delay': 60},
            {'flag': 'PutawayComplete', 'method': self.call_putaway_complete_program, 'mhe_delay': 60},
            {'flag': 'ASNVerify', 'method': self.call_asn_verify_program, 'mhe_delay': 30},
        ]

        for entry in worksheet_entries:
            logging.info(f"Processing entry: {entry}")

            if entry.get("RunAll") == 'Y':
                for op in operations:
                    if op['flag'] != 'ExceptionFlow':
                        op['method']()
                time.sleep(30)  # Final delay for RunAll
                self.call_mhe_journal_inbound_program()
                logging.info("Run All Program Completed Successfully")
                continue

            # Find the first operation flagged with 'Y'
            start_index = -1
            for i, op in enumerate(operations):
                if entry.get(op['flag']) == 'Y':
                    start_index = i
                    break

            if start_index == -1:
                logging.info("No operation flags set to 'Y'. No output produced for this entry.")
                continue

            # Execute all operations from the starting point that are flagged with 'Y'
            methods_to_run = []
            last_op_with_mhe = None

            for i in range(start_index, len(operations)):
                op = operations[i]
                # This logic runs a contiguous block of 'Y's from the starting point
                if entry.get(op['flag']) == 'Y':
                    methods_to_run.append(op['method'])
                    if 'mhe_delay' in op:
                        last_op_with_mhe = op
                else:
                    break  # Stop at the first non-'Y' flag

            if methods_to_run:
                for method in methods_to_run:
                    method()

                # After the sequence, trigger MHE journal if required by the last step
                if last_op_with_mhe:
                    time.sleep(last_op_with_mhe['mhe_delay'])
                    self.call_mhe_journal_inbound_program()

                logging.info("Program Completed Successfully")
            else:
                # This case should not be reached due to the start_index check, but is here for safety
                logging.info("The combination provided doesn't match the requirement.")

if __name__ == "__main__":
    inbound_master = inbound_master_step()
    inbound_master.get_inbound_master_worksheet_extract()


# Do not delete this as this is the version 1 of my learning.
# # Version 1
#
# import logging
# import pandas as pd
# import time
#
# from Payload_generation.Worksheet_extract import Worksheet
# from ASN_Creation import ASN_Creation
# from Inbound_Delivery import Inbound_Delivery
# from Good_Holder_Announced import Goods_Holder_Announced
# from Goods_Holder_Measured import Goods_Holder_Measured
# from Putaway_Complete import Putaway_Complete
# from ASN_Verify import ASN_Verify
# from MHE_Jounal_IB import MHE_Journal_Inbound
#
#
# class inbound_master_step:
#
#     def __init__(self):
#         """Initialize all service classes once to be reused."""
#         self.worksheet_extractor = Worksheet()
#         self.asn_creation = ASN_Creation()
#         self.inbound_delivery = Inbound_Delivery()
#         self.goods_holder_announced = Goods_Holder_Announced()
#         self.goods_holder_measured = Goods_Holder_Measured()
#         self.putaway_complete = Putaway_Complete()
#         self.asn_verify = ASN_Verify()
#         self.mhe_journal_inbound = MHE_Journal_Inbound()
#
#     def is_no_or_empty(self, value):
#         return value == 'N' or pd.isna(value) or value is None
#
#     def call_asn_creation_program(self):
#         # Calling the Create ASN function
#         logging.info("ASN Creation Program Started Successfully")
#         self.asn_creation.create_asns()
#         logging.info("ASN Created Program Completed Successfully")
#         time.sleep(5)
#         print("\n")
#
#     def call_inbound_delivery_program(self):
#         # Calling the inbound delivery function
#         logging.info("Inbound Delivery Program Started Successfully")
#         self.inbound_delivery.send_inbound_delivery()
#         logging.info("Inbound Delivery Created Successfully and triggered the pre receipt allocation")
#         time.sleep(5)
#         print("\n")
#
#     def call_goods_holder_announced_program(self):
#         # Calling the goods holder announced function
#         logging.info("Goods Holder Announced Program Started Successfully")
#         self.goods_holder_announced.send_goods_holder_announced()
#         logging.info("Goods Holder Announced Completed Successfully")
#         time.sleep(5)
#         print("\n")
#
#     def call_goods_holder_measured_program(self):
#         # Calling the goods holder measured function.
#         logging.info("Goods Holder Measured Program Started Successfully")
#         self.goods_holder_measured.send_goods_holder_measured()
#         logging.info("Goods Holder Measured Program Completed Successfully")
#         time.sleep(5)
#         print("\n")
#
#     def call_putaway_complete_program(self):
#         # Calling the Putaway Complete Function.
#         logging.info("Putaway Completed Program Started Successfully")
#         self.putaway_complete.create_putaway_task_complete()
#         logging.info("Putaway Completed Successfully")
#         time.sleep(5)
#         print("\n")
#
#     def call_asn_verify_program(self):
#         # Calling the ASN Verification Function
#         logging.info("ASN Verification Started Successfully")
#         self.asn_verify.send_asn_verify()
#         logging.info("ASN Verified Successfully")
#         time.sleep(5)
#         print("\n")
#
#     def call_mhe_journal_inbound_program(self):
#         # Calling the Message Journal Program
#         logging.info("Message Journal Program Started Successfully")
#         self.mhe_journal_inbound.create_mhe_journal_inbound()
#         logging.info("Message Journal Program Completed Successfully")
#
#     def get_inbound_master_worksheet_extract(self):
#         get_entry = self.worksheet_extractor.extract_master_sheet_from_worksheet()
#
#         if not get_entry:
#             logging.error("The worksheet returned nothing check worksheet program extract_master_sheet_from_worksheet function.")
#             return None
#
#         for entry in get_entry:
#             create_asn = entry.get("CreateASN", 'Y')
#             inbound_delivery = entry.get("InboundDelivery")
#             goods_holder_announced = entry.get("GH_Announced")
#             goods_holder_weighed = entry.get("GH_Weighed")
#             putaway_complete = entry.get("PutawayComplete")
#             asn_verify = entry.get("ASNVerify")
#             run_all = entry.get("RunAll", 'N')
#
#             if (create_asn == 'Y' and self.is_no_or_empty(inbound_delivery)
#                 and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
#                 and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):
#
#                 self.call_asn_creation_program()
#                 logging.info("Program Completed Successfully")
#                 print("\n")
#
#             elif (create_asn == 'Y' and inbound_delivery == 'Y' and self.is_no_or_empty(goods_holder_announced) and
#                   self.is_no_or_empty(goods_holder_weighed) and self.is_no_or_empty(putaway_complete) and
#                   self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):
#
#                 # Calling the Create ASN function
#                 self.call_asn_creation_program()
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#
#                 logging.info("Program Completed Successfully")
#
#             elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and self.is_no_or_empty(goods_holder_weighed)
#                 and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):
#
#                 # Calling the Create ASN function
#                 self.call_asn_creation_program()
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#
#                 time.sleep(35)
#                 # Calling the MHE journal program
#                 self.call_mhe_journal_inbound_program()
#
#                 logging.info("Program Completed Successfully")
#
#             elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y'
#                   and self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):
#
#                 # Calling the Create ASN function
#                 self.call_asn_creation_program()
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#
#                 time.sleep(35)
#
#                 print("\n")
#                 self.call_mhe_journal_inbound_program()
#
#                 logging.info("Program Completed Successfully")
#
#             elif (create_asn == 'Y' and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and goods_holder_weighed == 'Y' and
#                     putaway_complete == 'Y' and self.is_no_or_empty(asn_verify) and self.is_no_or_empty(run_all)):
#
#                 # Calling the Create ASN function
#                 self.call_asn_creation_program()
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#
#                 time.sleep(30)
#
#                 # Calling the MHE journal program
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and inbound_delivery == 'Y' and goods_holder_announced == 'Y' and
#                   goods_holder_weighed == 'Y' and putaway_complete == 'Y' and asn_verify == 'Y' and
#                   self.is_no_or_empty(run_all)):
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#
#                 time.sleep(30)
#
#                 # Calling the MHE journal program
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   goods_holder_announced == 'Y' and goods_holder_weighed == 'Y' and putaway_complete == 'Y' and
#                   asn_verify == 'Y' and self.is_no_or_empty(run_all)):
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#
#                 time.sleep(30)
#
#                 # Calling the MHE journal program
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   self.is_no_or_empty(goods_holder_announced) and goods_holder_weighed == 'Y' and
#                   putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#
#                 # Deliberately creating delay of 5 seconds for each function execution
#                 time.sleep(30)
#
#                 # Calling the MHE journal program
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
#                   putaway_complete == 'Y' and asn_verify == 'Y' and self.is_no_or_empty(run_all)):
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#
#                 # Deliberately creating delay of 30 seconds for each function execution
#                 time.sleep(30)
#
#                 # Calling the MHE journal program
#                 self.call_mhe_journal_inbound_program()
#
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
#                   self.is_no_or_empty(putaway_complete) and asn_verify == 'Y' and self.is_no_or_empty(run_all)):
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery)
#                 and self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed)
#                 and self.is_no_or_empty(putaway_complete) and run_all == 'Y'):
#
#                 # Calling the Create ASN function
#                 self.call_asn_creation_program()
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#
#                 # Deliberately creating delay of 5 seconds for each function execution
#                 time.sleep(30)
#
#                 # Calling the MHE Journal function.
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Run All Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and inbound_delivery == 'Y' and
#                   self.is_no_or_empty(goods_holder_announced) and  self.is_no_or_empty(goods_holder_weighed) and
#                   self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
#                   self.is_no_or_empty(run_all)):
#
#                 # Calling the inbound delivery function
#                 self.call_inbound_delivery_program()
#                 logging.info("Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   goods_holder_announced == 'Y' and  self.is_no_or_empty(goods_holder_weighed) and
#                   self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
#                   self.is_no_or_empty(run_all)):
#
#                 # Calling the goods holder announced function
#                 self.call_goods_holder_announced_program()
#                 logging.info("Program Completed Successfully")
#                 time.sleep(30)
#
#                 # Calling the MHE Journal function.
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Run All Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   self.is_no_or_empty(goods_holder_announced) and  goods_holder_weighed == 'Y' and
#                   self.is_no_or_empty(putaway_complete) and self.is_no_or_empty(asn_verify) and
#                   self.is_no_or_empty(run_all)):
#
#                 # Calling the goods holder measured function.
#                 self.call_goods_holder_measured_program()
#                 logging.info("Program Completed Successfully")
#                 time.sleep(30)
#
#                 # Calling the MHE Journal function.
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Run All Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
#                   putaway_complete == 'Y' and self.is_no_or_empty(asn_verify) and
#                   self.is_no_or_empty(run_all)):
#
#                 # Calling the Putaway Complete Function.
#                 self.call_putaway_complete_program()
#                 logging.info("Program Completed Successfully")
#                 time.sleep(30)
#
#                 # Calling the MHE Journal function.
#                 self.call_mhe_journal_inbound_program()
#                 logging.info("Run All Program Completed Successfully")
#
#             elif (self.is_no_or_empty(create_asn) and self.is_no_or_empty(inbound_delivery) and
#                   self.is_no_or_empty(goods_holder_announced) and self.is_no_or_empty(goods_holder_weighed) and
#                   self.is_no_or_empty(putaway_complete) and asn_verify == 'Y' and
#                   self.is_no_or_empty(run_all)):
#
#                 # Calling the ASN Verification Function
#                 self.call_asn_verify_program()
#                 logging.info("Program Completed Successfully")
#
#             else:
#                 logging.info(f"The combination provided doesnt match the requirement "
#                              f"therefore the program didnt produce any output.")
#
#
# inbound_master = inbound_master_step()
# inbound_master.get_inbound_master_worksheet_extract()