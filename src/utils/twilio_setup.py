from twilio.rest import Client


class TwilioSingleton:
    """Returns singleton object for twilio.
    This is just meant to be called once to complete the setup for twilio

    Ref: https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm
    """

    _instance = None

    def __init__(self, base_path="/secrets"):

        fs_twilio_account_sid = open(
            f"{base_path}/twilio_account_sid/twilio_account_sid", "r"
        )
        twilio_account_sid = fs_twilio_account_sid.readlines()[0].strip()
        fs_twilio_auth_token = open(
            f"{base_path}/twilio_auth_token/twilio_auth_token", "r"
        )
        twilio_auth_token = fs_twilio_auth_token.readlines()[0].strip()
        fs_twilio_service_sid = open(
            f"{base_path}/twilio_verify_service_sid/twilio_verify_service_sid", "r"
        )
        twilio_service_sid = fs_twilio_service_sid.readlines()[0].strip()

        self.acc_sid = twilio_account_sid
        self.secret = twilio_auth_token
        self.sid = twilio_service_sid

    @classmethod
    def client(self, cls):
        if cls._instance is None:
            cls._instance = Client(self.acc_sid, self.secret).verify.v2.services(
                self.sid
            )

        return cls._instance
