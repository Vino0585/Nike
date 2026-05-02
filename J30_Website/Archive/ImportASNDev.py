import requests
import json
from datetime import datetime
import random
from Token import Token

# Getting the token.
token_handler = Get_Token()
gen_bearer = token_handler.get_bearer()

# Variables for payload
host_name = 'nikeaplawmdev1.sce.manh.com'
asn_id = f"VGASN{datetime.today().strftime('%d%m%y')}{random.randint(10, 99)}" # VG0250108100026
lpn_id = f'000000VG{datetime.today().strftime('%d%m%Y')}{random.randint(1000, 9999)}' # 00000000108101081042
item = 'AC4081-014-MISC'
qty = 10

print(f"Following is the ASN ID {asn_id} for the item {item} with qty {qty}")

asn_url = f"https://{host_name}/receiving/api/receiving/asn/save"

payload = json.dumps(
{
    "AsnId": f"{asn_id}",
    "AsnOriginTypeId": "P",
    "VendorId": None,
    "OrgId": "1081",
    "DestinationFacilityId": "1081",
    "AsnStatus": "1000",
    "AsnLevel": "LPN",
    "Lpn": [
        {
            "AsnId": f"{asn_id}",
            "VendorId": None,
            "LpnId": f"{lpn_id}",
            "LpnStatus": "1000",
            "OrgId": "1081",
            "SingleItemLPN": "1",
            "LpnTypeId": "ILPN",
            "LpnDetail": [
                {
                    "AsnId": f"{asn_id}",
                    "ExpiryDate": "",
                    "InventoryAttribute1": "01000",
                    "CountryOfOrigin": "CN",
                    "ItemId": f"{item}",
                    "ManufacturingDate": "",
                    "QuantityUomId": "LPN",
                    "ShipByDate": "",
                    "ShippedQuantity": 5,
                    "PurchaseOrderId": "25050501",
                    "PurchaseOrderLineId": ""
                }]
        }
    ]
})

headers = {
    "Content-Type": "application/json",
    "selectedOrganization": '1081',
    "selectedLocation": '1081',
    "Authorization": 'Bearer ' + gen_bearer
}

response = requests.post(url=asn_url, headers=headers, data=payload)

get_response = response.json()
print(get_response)
print(F"Is it successful? {get_response['success']}\nElse What is the error? {get_response['messageKey']}")