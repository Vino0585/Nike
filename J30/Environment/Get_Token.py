import requests
import os


class Get_Token():

    # To get the bearer token
    # ----------------------------
    def __init__(self, env, plant):
        self.bearer_host_name = ''
        self.data = ''
        self.key = ''

        if env == 'qa' and plant == '1081':
            self.bearer_host_name = "https://nikeaplawmqa1-auth.sce.manh.com/oauth/token"
        elif env == 'prod' and plant == '1081':
            self.bearer_host_name = "https://nikip3-auth.sce.manh.com/oauth/token"
        elif env == 'dev' and plant == '1081':
            self.bearer_host_name = "https://nikeaplawmdev1-auth.sce.manh.com/oauth/token"
        elif env == 'qa' and plant == '1093':
            self.bearer_host_name = "https://nikeaplawmqa1-auth.sce.manh.com/oauth/token"
        else:
            print("No proper Environment is passed to token class.")

        self.payload = {
            "grant_type": "password",
            "username": "vgana3",
            "password": "Vino-35160626"
        }

        self.headers = {
            'Authorization': 'Basic b21uaWNvbXBvbmVudC4xLjAuMDpiNHM4cmdUeWc1NVhZTnVu',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def get_bearer(self):
        # SSL behavior can be controlled externally:
        # - NIKE_CA_BUNDLE=/path/to/cert.pem  (recommended)
        # - NIKE_DISABLE_SSL_VERIFY=true      (temporary workaround only)
        disable_ssl_verify = os.getenv("NIKE_DISABLE_SSL_VERIFY", "").strip().lower() in {"1", "true", "yes", "y"}
        ca_bundle = os.getenv("NIKE_CA_BUNDLE", "").strip() or os.getenv("REQUESTS_CA_BUNDLE", "").strip()
        verify = False if disable_ssl_verify else (ca_bundle if ca_bundle else True)

        response = requests.post(
            url=self.bearer_host_name,
            headers=self.headers,
            data=self.payload,
            verify=verify,
            timeout=30
        )
        response.raise_for_status()
        self.data = response.json()
        self.key = self.data["access_token"]
        # token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhQ1I2NlhmWWZRb1hkbUltaHFOWkxVSTZFVWpxVHZQaWNLSnRtdG1DTzlzIn0.eyJleHAiOjE3ODI3NDUzNzcsImlhdCI6MTc4MjcwMjE3NywianRpIjoiMjhiNWVmMzgtMGNjZi00YjhlLWJjMGItZmIzMWE3YjJkMDZiIiwiaXNzIjoiaHR0cHM6Ly9uaWtlYXBsYXdtcHJvZDEtYXV0aC5zY2UubWFuaC5jb20vYXV0aC9yZWFsbXMvbWFhY3RpdmUiLCJzdWIiOiJ2Z2FuYTMiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJvbW5pY29tcG9uZW50LjEuMC4wIiwic2Vzc2lvbl9zdGF0ZSI6IjNhMTIwNzFlLTAxZTItNDM4Mi04OTdhLTA0ZDhlZGJkMTQyYyIsImFjciI6IjEiLCJzY29wZSI6ImVtYWlsIGNvbXBvbmVudCBwcm9maWxlIG9wZW5pZCBvbW5pIiwic2lkIjoiM2ExMjA3MWUtMDFlMi00MzgyLTg5N2EtMDRkOGVkYmQxNDJjIiwidXNlck9yZ3MiOlsiQVBMQSIsIjEwODEiXSwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJ1c2VyX25hbWUiOiJ2Z2FuYTMiLCJ1c2VyTG9jYXRpb25zIjpbeyJsb2NhdGlvbklkIjoiMTA4MSIsImxvY2F0aW9uVHlwZSI6ImR1bW15In1dLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJ2Z2FuYTMiLCJnaXZlbl9uYW1lIjoiVmlub3Roa3VtYXIiLCJsb2NhbGUiOiJlbiIsImF1dGhvcml0aWVzIjpbIlJPTEVfVVNFUiIsIlJPTEVfQVBMQS1QQUMgT3JnIExvZ2luIl0sInVzZXJUaW1lWm9uZSI6IkF1c3RyYWxpYS9NZWxib3VybmUiLCJlZGdlIjoiMCIsIm9yZ2FuaXphdGlvbiI6IkFQTEEiLCJhY2Nlc3N0b0FsbEJVcyI6ZmFsc2UsInRlbmFudElkIjoibmlraXNwcjMxbyIsIm5hbWUiOiJWaW5vdGhrdW1hciBHYW5hcGF0aHkiLCJ1c2VyRGVmYXVsdHMiOlt7ImRlZmF1bHRCdXNpbmVzc1VuaXQiOm51bGwsImRlZmF1bHRMb2NhdGlvbiI6IjEwODEiLCJkZWZhdWx0T3JnYW5pemF0aW9uIjoiMTA4MSJ9XSwiZmFtaWx5X25hbWUiOiJHYW5hcGF0aHkiLCJlbWFpbCI6IlZpbm90aGt1bWFyLkdhbmFwYXRoeUBuaWtlLmNvbSJ9.c4KGPY7jx7AQtJr3_4bPKbvywBWs5q-AJ9G-OW9CTfsnkqRwmJRAhD2FQQDlbi6jE_4ikMj6o2uS_gIjy1wZEeA1xUFFpIi0umM129CZKScZXMR1DJZU55fWxXfLlxdvLjZ92RBDsu3wi6EuNbkzFVbgp7Y21aX9ZiUIMKXMkdlgWa5G6ZcwnSgnOGgVn3xyupeeC_nSLXhik3NUX6ddxfXDZNPrso9ozHOVs1ea0E7Oq8DNpOP0pvP2iFkPEDGFxITWEfQn8-gEtmVCsHIa1EbYbTuM0DGa1V8Q_mR2W-9ihOUU-OgkhFYt5XJsRNqmpEoTgvZo3D7XTOAYl7pMtg"
        return self.key
        # return token

    # Bearer token request completed -------------------------------

if __name__ == '__main__':
    bearer = Get_Token(env='prod', plant='1081')
    get_token = bearer.get_bearer()
    print(get_token)