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
        else:
            self.url = None  # Set to None if no match
        return self.url