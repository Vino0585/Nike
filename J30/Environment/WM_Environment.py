class AWM_Env():
    def __init__(self):
        self.host_name = ''
        self.url = ''
    def get_wm_host(self, host, facility):  # Removed 'program' here, as it's not directly used for host logic
        if host == 'dev' and facility == "1081":
            self.host_name = 'nikeaplawmdev1.sce.manh.com'
        elif host == 'qa' and facility == "1081":
            self.host_name = 'nikeaplawmqa1.sce.manh.com'
        else:
            self.host_name = 'default_host.com'  # Added a default for clarity

    def get_program_url(self, program):  # Made this a separate method
        if program == 'ASN_Creation':
            self.url = f"https://{self.host_name}/receiving/api/receiving/asn/save"
        elif program == 'ASN_Search':
            self.url = f"https://{self.host_name}/receiving/api/receiving/asn/search"
        elif program == 'Item_Search':
            self.url = f"https://{self.host_name}/item-master/api/item-master/item/search"
        elif program == 'Goods_Holder_Announced':
            self.url = f"https://{self.host_name}/device-integration/api/deviceintegration/process/NIKEGoodsholderAnnouncedSRCEndpointV1"
        elif program == 'Goods_Holder_Measured':
            self.url = f"https://{self.host_name}/device-integration/api/deviceintegration/process/NIKEGoodsholderMeasuredSRCEndpointV1"
        elif program == 'Search_Task_Detail':
            self.url = f"https://{self.host_name}/task/api/task/taskDetail/search"
        elif program == "Putaway_Task_Complete":
            self.url = f"https://{self.host_name}/device-integration/api/deviceintegration/process/NIKEPutawayTaskResultSRCEndpointV1"
        elif program == "Get_Inbound_Delivery":
            self.url = f"https://{self.host_name}/receiving/api/receiving/generateShipmentId"
        elif program == "Add_ASN_To_Inbound_Delivery":
            self.url = f"https://{self.host_name}/dmui-facade/api/dmui-facade/receiving/shipmentAsnAssociation/bulkImport"
        elif program == "Pre_Allocate_Inbound_Delivery":
            self.url = f"https://{self.host_name}/dmui-facade/api/dmui-facade/view/action/com-manh-cp-receiving/Shipment/PreAllocateShipment?"
        elif program == "ASN_Verify":
            self.url = f"https://{self.host_name}/dmui-facade/api/dmui-facade/receiving/ui/asn/verify"
        elif program == "Message_Journal_Inbound":
            self.url = f"https://{self.host_name}/dmui-facade/api/dmui-facade/entity/search"
        elif program == "iLPN_Information_Receiving":
            self.url = f"https://{self.host_name}/receiving/api/receiving/lpn/search"
        elif program == "iLPN_Information_Inventory":
            self.url = f"https://{self.host_name}/dcinventory/api/dcinventory/ilpn/search"
        elif program == "Routing_Task_Completed":
            self.url = f"https://{self.host_name}/device-integration/api/deviceintegration/process/NIKERoutingTaskResultSRCEndpointV1"
        elif program == 'iLPN_Receiving':
            self.url = f"https://{self.host_name}/receiving/api/receiving/lpn/search"
        elif program == 'iLPN_Inventory':
            self.url = f"https://{self.host_name}/dcinventory/api/dcinventory/ilpn/search"
        elif program == 'iLPN_Condition_Code':
            self.url = f"https://{self.host_name}/dcinventory/api/dcinventory/containerConditionVisibility/search"
        elif program == 'Recall_Retrieval_Task_Complete':
            self.url = f"https://{self.host_name}/device-integration/api/deviceintegration/process/NIKERetrievalTaskResultSRCEndpointV1"
        elif program == 'Item_Inventory_By_Location':
            self.url = f"https://{self.host_name}/dmui-facade/api/dmui-facade/inventory/grid/search"
        elif program == 'Tran_log_detail_header':
            self.url = f"https://{self.host_name}/fwuifacade/api/fwuifacade/entity/search"
        elif program == 'Tran_log_detail':
            self.url = f"https://{self.host_name}/fwuifacade/api/fwuifacade/entity/invoke?componentName=com-manh-cp-xint&url=/api/xint/payload/getByMessageId/"
        else:
            self.url = None  # Set to None if no match

        return self.url