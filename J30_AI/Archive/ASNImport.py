# import pandas as pd
# import openpyxl
# from datetime import datetime
# import random
# import json
#
# # Getting the token.
# token_handler = GET_Token()
# gen_bearer = token_handler.get_bearer()
#
# # Get the excel file info.
#
# excel_file_path = '../ImportASN/WorkSheet.xlsx'
# data_dict_index = {}
#
# try:
#     xls = pd.ExcelFile(excel_file_path)
#     sheet_names = xls.sheet_names
#     print(f"Sheets found in '{excel_file_path}': {sheet_names}")
#
#     df = pd.read_excel(excel_file_path, sheet_name='ASN')
#     print("\nData from 'Sheet1':")
#     data_dict_index = df.to_dict(orient='index')[0]
#
# except FileNotFoundError:
#     print(f"Error: The file '{excel_file_path}' was not found.")
# except Exception as e:
#     print(f"An error occurred: {e}")
#
# # Extract data from the dictionary
# plant = data_dict_index.get("Plant")
# num_of_asn = int(data_dict_index.get('Number of ASN', 0)) # Default to 0 if not found
# item = data_dict_index.get("Item")
# qty = int(data_dict_index.get('Qty', 0))
# case_qty = int(data_dict_index.get('Case qty', 1)) # Default to 1 to avoid division by zero
#
# print(f"Number of ASN: {num_of_asn}, Item: {item}, Quantity: {qty}, Case Quantity: {case_qty}")
#
# # --- Generate ASN IDs ---
# asn_ids = []
# if num_of_asn > 0:
#     for _ in range(num_of_asn):
#         asn_ids.append(f"VGASN{datetime.today().strftime('%d%m%y')}{random.randint(10, 99)}")
# else:
#     print("Warning: Number of ASN is zero or invalid. No ASN IDs will be generated.")
#
# # --- Generate LPN IDs ---
# # Determine how many LPNs per ASN. For simplicity, we'll divide total LPNs needed by num_of_asn.
# # If you need specific LPN distributions, this logic will need adjustment.
# num_of_lpn_total = 0
# if case_qty > 0:
#     num_of_lpn_total = int(qty / case_qty) * num_of_asn
# else:
#     print("Warning: Case quantity is zero, cannot calculate number of LPNs.")
#
# if num_of_lpn_total == 0:
#     print("Warning: The calculated number of LPNs is zero. No LPNs will be generated.")
#
# # Store generated payloads
# all_asn_payloads = []
#
# # --- Create Payload for Each ASN ---
# # --- Create Payload for Each ASN ---
# if asn_ids: # Proceed only if ASN IDs were generated
#     lpn_counter = 0 # To distribute LPNs among ASNs
#     for i, current_asn_id in enumerate(asn_ids):
#         lpn_list_for_current_asn = []
#
#         num_lpns_for_this_asn = num_of_lpn_total / num_of_asn
#         #  3 = 6 / 2
#
#         remaining_lpns = num_of_lpn_total - (
#                     i * (num_of_lpn_total // num_of_asn)) if num_of_asn > 0 else num_of_lpn_total
#
#         if num_of_asn > 0 and remaining_lpns > 0:
#             # Distribute remaining LPNs somewhat evenly
#             num_lpns_for_this_asn = int(num_of_lpn_total // num_of_asn)
#             if i < (num_of_lpn_total % num_of_asn):  # Distribute remainder
#                 num_lpns_for_this_asn += 1
#
#             print(num_lpns_for_this_asn)
#
#         for _ in range(num_lpns_for_this_asn):
#             # Generate a unique LPN ID for each LPN within the current ASN
#             current_lpn_id = f'000000VG{datetime.today().strftime('%d%m%Y')}{random.randint(1000, 9999)}{lpn_counter}'
#             lpn_counter += 1  # Ensure unique LPN IDs across all ASNs
#
#             lpn_detail_data = {
#                 "AsnId": current_asn_id,
#                 "ExpiryDate": "",
#                 "InventoryAttribute1": "01000",
#                 "CountryOfOrigin": "CN",
#                 "ItemId": item,  # Use the item from excel
#                 "ManufacturingDate": "",
#                 "QuantityUomId": "LPN",
#                 "ShipByDate": "",
#                 "ShippedQuantity": case_qty,  # Quantity per LPN should be case_qty
#                 "PurchaseOrderId": "25050501",
#                 "PurchaseOrderLineId": ""
#             }
#
#             lpn_data = {
#                 "AsnId": current_asn_id,
#                 "VendorId": None,
#                 "LpnId": current_lpn_id,
#                 "LpnStatus": "1000",
#                 "OrgId": plant,
#                 "SingleItemLPN": "1",
#                 "LpnTypeId": "ILPN",
#                 "LpnDetail": [lpn_detail_data]  # LpnDetail is a list of item details for this LPN
#             }
#             lpn_list_for_current_asn.append(lpn_data)
#
#         # Construct the full payload for the current ASN
#         asn_payload = {
#             "AsnId": current_asn_id,
#             "AsnOriginTypeId": "P",
#             "VendorId": None,
#             "OrgId": plant,
#             "DestinationFacilityId": "1081",
#             "AsnStatus": "1000",
#             "AsnLevel": "LPN",
#             "Lpn": lpn_list_for_current_asn
#         }
#
#         all_asn_payloads.append(json.dumps(asn_payload, indent=4))  # Add formatted JSON string
#
# # Print all generated payloads
# for i, payload in enumerate(all_asn_payloads):
#     print(f"\n--- Payload for ASN {i+1} ({asn_ids[i]}) ---")
#     print(payload)
#
# if not all_asn_payloads:
#     print("\nNo payloads were generated. Please check your Excel input and logic.")
#
# headers = {
#     "Content-Type": "application/json",
#     "selectedOrganization": plant,
#     "selectedLocation": plant,
#     "Authorization": 'Bearer ' + gen_bearer
# }
#
#
# host_name = 'nikeaplawmdev1.sce.manh.com'
# asn_url = f"https://{host_name}/receiving/api/receiving/asn/save"
#
# response = requests.post(url=asn_url, headers=headers, data=payload)
#
# get_response = response.json()
# print(get_response)
# print(F"Is it successful? {get_response['success']}\nElse What is the error? {get_response['messageKey']}")