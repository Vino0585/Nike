import requests

class Get_Token():

    # To get the bearer token
    # ----------------------------
    def __init__(self, env, plant):
        self.bearer_host_name = ''
        self.data = ''
        self.key = ''

        if env == 'qa' and plant == '1081':
            self.bearer_host_name = "https://nikeaplawmqa1-auth.sce.manh.com/oauth/token"
        elif env == 'dev' and plant == '1081':
            self.bearer_host_name = "https://nikeaplawmdev1-auth.sce.manh.com/oauth/token"
        else:
            print("No proper Environment is passed to token class.")

        self.payload = {
            "grant_type": "password",
            "username": "vgana3",
            "password": "Vino-35160825"
        }

        self.headers = {
            'Authorization': 'Basic b21uaWNvbXBvbmVudC4xLjAuMDpiNHM4cmdUeWc1NVhZTnVu',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def get_bearer(self):
        response = requests.post(url=self.bearer_host_name, headers=self.headers, data=self.payload)
        self.data = response.json()
        self.key = self.data["access_token"]
        return self.key

    # Bearer token request completed -------------------------------
