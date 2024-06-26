from twilio.rest import Client


class TwilioSingleton:
    """Returns singleton object for twilio.
    This is just meant to be called once to complete the setup for twilio

    Ref: https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_singleton.htm
    """

    _instance = None
    _sid = None
    _secret = None
    _acc_id = None

    def __init__(self):
        raise Exception("Twilio is already initialiazed")

    @classmethod
    def client(cls, base_path="/"):
        if cls._instance is None:
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
            cls._instance = Client(
                twilio_account_sid, twilio_auth_token
            ).verify.v2.services(twilio_service_sid)
        return cls._instance

    @classmethod
    def token(cls, base_path="/"):
        if cls._sid is None or cls._secret is None or cls._acc_id is None:
            fs_twilio_video_sid = open(
                f"{base_path}/twilio_video_sid/twilio_video_sid", "r"
            )
            twilio_video_sid = fs_twilio_video_sid.readlines()[0].strip()
            fs_twilio_video_account_sid = open(
                f"{base_path}/twilio_video_account_sid/twilio_video_account_sid", "r"
            )
            twilio_video_account_sid = fs_twilio_video_account_sid.readlines()[
                0
            ].strip()
            fs_twilio_video_secret = open(
                f"{base_path}/twilio_video_secret/twilio_video_secret", "r"
            )
            twilio_video_secret = fs_twilio_video_secret.readlines()[0].strip()
            cls._sid = twilio_video_sid
            cls._secret = twilio_video_secret
            cls._acc_id = twilio_video_account_sid
        return (cls._sid, cls._secret, cls._acc_id)
