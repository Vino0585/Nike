import uuid
import datetime as dt

from ASN_Search import create_from_asn_list_of_lpn
from Payload_generation.Worksheet_extract import Worksheet
from Payload_generation.Task_Search_Payload import Task_Search_Payload


class Payload_Complete_Payload:

    def __init__(self):
        self.worksheet = Worksheet()
        self.task_search = Task_Search_Payload()
        # This instance variable isn't strictly necessary if only used in one method,
        # but we'll keep it for consistency with your original structure.
        self.all_putaway_complete_payload = []


    def create_putaway_complete_payloads(self) -> list:
        """
        Generates a list of GOODSHOLDER_ANNOUNCED payloads from worksheet data.
        """
        putaway_complete_data = self.worksheet.putaway_task_complete()

        if not putaway_complete_data:
            print("No valid item parameters found, cannot create any payloads for putaway complete task.")
            return []

        payloads = []
        get_task_list_response = {}
        get_task_payload = []

        for entry in putaway_complete_data:
            plant = entry.get("Plant")
            envn = entry.get("Environment")
            lpn_id_string = entry.get("LPN_ID")
            asn_id = entry.get("ASN")
            # get_list_from_asn_search = []
            # # asn_list = []
            # # lpn_list = []
            # # if asn_id:
            # #     asn_list = asn_id.split(';')
            # #     for asn in
            # #     get_list_from_asn_search = create_from_asn_list_of_lpn()
            # #     if not get_list_from_asn_search:
            # #         print("ASN entered in worksheet but couldn't get information from ASN search program check the ASN program for error")
            # #
            # #     for entry in get_list_from_asn_search:
            # #         lpn_list.append(entry.get("LpnId"))
            # #
            # # print(lpn_list)
            #
            # get_task_list_response = self.task_search.search_task_detail_payloads(lpn_id_string, envn, plant)
            # get_task_payload = get_task_list_response['data']
            # if not get_task_payload:
            #     print(f"Task_search_payload returned nothing or having error")
            #
            # for each_entry in get_task_payload:
            #     inbound_lpn = each_entry.get("SourceContainerId")
            #     dest_locn = each_entry.get("TargetLocationId")
            #     task_id = each_entry.get("TaskId")

            if not lpn_id_string:
                print("No LPN is given")
                continue

            lpn_in_list = lpn_id_string.split(";")

            for lpn in lpn_in_list:
                aware_timestamp = dt.datetime.now(dt.timezone.utc)
                iso_timestamp_str = aware_timestamp.isoformat()
                event_id = str(uuid.uuid4())

                putaway_each_payload = {
                    "event": {
                        "type": "PUTAWAY_TASK_COMPLETED",
                        "tmst": iso_timestamp_str,
                        "id": event_id,
                        "correlationId": None,
                        "distributionCenterCd": f"NODE_{plant}",
                        "technicalSolutionSourceCd": "NAS_V001",
                        "version": "1.0.0"
                    },
                    "data": {
                        "distributionCenterCd": f"NODE_{plant}",
                        "taskId": f"T-1234324",
                        "goodsholderId": f"{lpn}",
                        "putawayTaskCompleted": {
                            "storedAtLogicalStorageLocationId": f"2401000001",
                            "substitutionlockActivated": "false",
                            "confirmedByDeviceId": "12345678"
                        },
                        "executionTmst": iso_timestamp_str
                    }
                }

                ptwy_payload = {
                    'environment': envn,
                    'plant': plant,
                    'PTWYCPayload': putaway_each_payload
                }

                self.all_putaway_complete_payload.append(ptwy_payload)

            print(f"\nSuccessfully created {len(self.all_putaway_complete_payload)} payload generation(s) and sent to the program that called this function")

        return self.all_putaway_complete_payload

# initiation = Payload_Complete_Payload()
# payload = initiation.create_putaway_complete_payloads()
# print(payload)

# ---------      Very Important dont delete     --------------------
# # Version 1 To get task from task search payload
#
# import uuid
# import datetime as dt
#
# from ASN_Search import create_from_asn_list_of_lpn
# from Payload_generation.Worksheet_extract import Worksheet
# from Payload_generation.Task_Search_Payload import Task_Search_Payload
#
#
# class Payload_Complete_Payload:
#
#     def __init__(self):
#         self.worksheet = Worksheet()
#         self.task_search = Task_Search_Payload()
#         # This instance variable isn't strictly necessary if only used in one method,
#         # but we'll keep it for consistency with your original structure.
#         self.all_putaway_complete_payload = []
#
#
#     def create_putaway_complete_payloads(self) -> list:
#         """
#         Generates a list of GOODSHOLDER_ANNOUNCED payloads from worksheet data.
#         """
#         putaway_complete_data = self.worksheet.putaway_task_complete()
#
#         if not putaway_complete_data:
#             print("No valid item parameters found, cannot create any payloads for putaway complete task.")
#             return []
#
#         payloads = []
#         get_task_list_response = {}
#         get_task_payload = []
#
#         for entry in putaway_complete_data:
#             plant = entry.get("Plant")
#             envn = entry.get("Environment")
#             lpn_id_string = entry.get("LPN_ID")
#             asn_id = entry.get("ASN")
#             get_list_from_asn_search = []
#             # asn_list = []
#             # lpn_list = []
#             # if asn_id:
#             #     asn_list = asn_id.split(';')
#             #     for asn in
#             #     get_list_from_asn_search = create_from_asn_list_of_lpn()
#             #     if not get_list_from_asn_search:
#             #         print("ASN entered in worksheet but couldn't get information from ASN search program check the ASN program for error")
#             #
#             #     for entry in get_list_from_asn_search:
#             #         lpn_list.append(entry.get("LpnId"))
#             #
#             # print(lpn_list)
#
#             get_task_list_response = self.task_search.search_task_detail_payloads(lpn_id_string, envn, plant)
#             get_task_payload = get_task_list_response['data']
#             if not get_task_payload:
#                 print(f"Task_search_payload returned nothing or having error")
#
#             for each_entry in get_task_payload:
#                 inbound_lpn = each_entry.get("SourceContainerId")
#                 dest_locn = each_entry.get("TargetLocationId")
#                 task_id = each_entry.get("TaskId")
#
#                 aware_timestamp = dt.datetime.now(dt.timezone.utc)
#                 iso_timestamp_str = aware_timestamp.isoformat()
#                 event_id = str(uuid.uuid4())
#
#                 putaway_each_payload = {
#                     "event": {
#                         "type": "PUTAWAY_TASK_COMPLETED",
#                         "tmst": iso_timestamp_str,
#                         "id": event_id,
#                         "correlationId": None,
#                         "distributionCenterCd": f"NODE_{plant}",
#                         "technicalSolutionSourceCd": "NAS_V001",
#                         "version": "1.0.0"
#                     },
#                     "data": {
#                         "distributionCenterCd": f"NODE_{plant}",
#                         "taskId": f"{task_id}",
#                         "goodsholderId": f"{inbound_lpn}",
#                         "putawayTaskCompleted": {
#                             "storedAtLogicalStorageLocationId": f"{dest_locn}",
#                             "substitutionlockActivated": "false",
#                             "confirmedByDeviceId": "12345678"
#                         },
#                         "executionTmst": iso_timestamp_str
#                     }
#                 }
#
#                 ptwy_payload = {
#                     'environment': envn,
#                     'plant': plant,
#                     'PTWYCPayload': putaway_each_payload
#                 }
#
#                 self.all_putaway_complete_payload.append(ptwy_payload)
#
#             print(f"\nSuccessfully created {len(self.all_putaway_complete_payload)} payload generation(s) and sent to the program that called this function")
#
#         return self.all_putaway_complete_payload