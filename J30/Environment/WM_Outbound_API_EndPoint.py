class AWM_OB_Env():

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

    def get_program_url(self, program):
        if program == 'OrderCreation':
            self.url = f"https://{self.host_name}/dcorder/api/dcorder/originalOrder/save"
        elif program == 'CreateShipment':
            self.url = f"https://{self.host_name}/shipment/api/ServiceDefinition/invoke/NIKEINT10CreateShipmentCS"
        elif program == "AddOrderToShipment":
            self.url = f"https://{self.host_name}/dcorder/api/ServiceDefinition/invoke/NIKEINT10OriginalOrderUpdateCS"
        elif program == "ParentOrderSearch":
            self.url = f"https://{self.host_name}/dmui-facade/api/dmui-facade/entity/search"
        elif program == "ParentOrderSearchBackup":
            self.url = f"https://{self.host_name}/dcorder/api/dcorder/order/search"
        elif program == 'Search_Task_Detail':
            self.url = f"https://{self.host_name}/task/api/task/taskDetail/search"
        else:
            self.url = None

        return self.url