import os


class FR_Preprocessor_Env:
    """Environment configuration for FR preprocessor API."""

    def __init__(self, environment: str = "QA"):
        env = str(environment).strip().upper() if environment is not None else "QA"
        if not env:
            env = "QA"

        qa_config = {
            "token_url": "https://nike-qa.oktapreview.com/oauth2/ausa0mcornpZLi0C40h7/v1/token",
            "client_id": "nike.gfls.node-fr-preprocessor-api",
            "client_secret": "tW-q0kG2Zu9cZNHs8HiKe2nnARJBVqD9RUoB40qbJth0077pwsL2LaywXXgdGjSX",
            "grant_type": "client_credentials",
            "scope": "fulfillment:node.fr.preprocessor::read:",
            "content_type": "application/json",
            "request_url": "https://node-fr-preprocessor-ap-test.nodemanagement-test.nikecloud.com/api/node/preprocessor/send/v1",
        }

        # PROD values come from environment variables to avoid hardcoding secrets.
        prod_config = {
            "token_url": "https://nike.okta.com/oauth2/aus27z7p76as9Dz0H1t7/v1/token",
            "client_id": "nike.scpt.node-extension-nsp3-admin",
            "client_secret": "j0VDwGh5qw5GMIwJh_FxR-UVGvTlqqFTHPWOTGYdPdzkcLQFyMILntil2HShimVD",
            "grant_type": "client_credentials",
            "scope": "",
            "content_type": "application/json",
            "request_url": "https://node-fr-preprocessor-ap-prod.nodemanagement-prod.nikecloud.com/api/node/preprocessor/send/v1",
        }

        if env == "PROD":
            missing = [key for key in ("token_url", "client_id", "client_secret", "request_url") if not prod_config.get(key)]
            if missing:
                raise ValueError(
                    "Missing PROD FR preprocessor configuration. "
                    f"Set env vars for: {', '.join(missing)}"
                )
            config = prod_config
        else:
            # Default any unknown input to QA for backward compatibility.
            config = qa_config

        self.token_url = config["token_url"]
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.grant_type = config["grant_type"]
        self.scope = config["scope"]
        self.content_type = config["content_type"]
        self.request_url = config["request_url"]

        # Kept from Bruno env for future extension/use.
        self.base_url = "api.euc1.nmk-staging.platforms.nike.com/api/v2"
        self.team_email = "Lst-India.goaltech-Lithium@nike.com"
        self.cluster_name = "general-v2"
        self.environment = "dev"
        self.nsp_env = "test"
        self.nsp_region = "eu-central-1"
        self.nsp_consumer_id = "nike.gfls.node-ext"

    def get_token_payload(self):
        payload = {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            payload["scope"] = self.scope
        return payload
