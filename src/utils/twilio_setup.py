from twilio.rest import Client


class TwilioSingleton:
    """Returns singleton object for twilio.
    This is just meant to be called once to complete the setup for twilio

    Ref: https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm
    """

    _instance = None

    def __init__(self):
        raise Exception("Twilio is already initialiazed")

    @classmethod
    def client(cls):
        if cls._instance is None:
            fs_twilio_account_sid = open("/twilio_account_sid/twilio_account_sid", "r")
            twilio_account_sid = fs_twilio_account_sid.readlines()[0].strip()
            fs_twilio_auth_token = open("/twilio_auth_token/twilio_auth_token", "r")
            twilio_auth_token = fs_twilio_auth_token.readlines()[0].strip()
            fs_twilio_service_sid = open(
                "/twilio_verify_service_sid/twilio_verify_service_sid", "r"
            )
            twilio_service_sid = fs_twilio_service_sid.readlines()[0].strip()
            cls._instance = Client(
                twilio_account_sid, twilio_auth_token
            ).verify.v2.services(twilio_service_sid)
        return cls._instance
