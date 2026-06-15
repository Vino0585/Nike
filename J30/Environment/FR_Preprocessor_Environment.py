class FR_Preprocessor_Env:
    """Environment configuration for NSP2.0 dev preprocessor API."""

    def __init__(self):
        self.token_url = "https://nike-qa.oktapreview.com/oauth2/ausa0mcornpZLi0C40h7/v1/token"
        self.client_id = "nike.gfls.node-fr-preprocessor-api"
        self.client_secret = "tW-q0kG2Zu9cZNHs8HiKe2nnARJBVqD9RUoB40qbJth0077pwsL2LaywXXgdGjSX"
        self.grant_type = "client_credentials"
        self.scope = "fulfillment:node.fr.preprocessor::read:"
        self.content_type = "application/json"
        self.request_url = "https://node-fr-preprocessor-ap-test.nodemanagement-test.nikecloud.com/api/node/preprocessor/send/v1"

        # Kept from Bruno env for future extension/use.
        self.base_url = "api.euc1.nmk-staging.platforms.nike.com/api/v2"
        self.team_email = "Lst-India.goaltech-Lithium@nike.com"
        self.cluster_name = "general-v2"
        self.environment = "dev"
        self.nsp_env = "test"
        self.nsp_region = "eu-central-1"
        self.nsp_consumer_id = "nike.gfls.node-ext"

    def get_token_payload(self):
        return {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }
