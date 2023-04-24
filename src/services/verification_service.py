from twilio.base.exceptions import TwilioRestException

from utils.twilio_setup import TwilioSingleton

ALLOWED_CHANNELS = ["email", "sms"]
SUPPORTED_LOCALES = ["en", "ja"]


class VerificationService:
    def __init__(self, service=None) -> None:
        self._service = service or TwilioSingleton.client()

    def start_verification(
        self, to: str, channel: str, locale: str
    ) -> tuple[Exception, str]:
        if channel not in ALLOWED_CHANNELS:
            return (
                Exception(f"Channel {channel} is not allowed: {ALLOWED_CHANNELS}"),
                None,
            )
        if locale not in SUPPORTED_LOCALES:
            return (
                Exception(f"Locale {locale} is not supported: {SUPPORTED_LOCALES}"),
                None,
            )

        try:
            verification = self._service.verifications.create(to=to, channel=channel)
        except TwilioRestException as e:
            if e.status == 400 and "Invalid parameter" in e.msg:
                return Exception(f"bad start_verification call: {e.msg}"), None
            # bubble up unexpected exception
            raise e

        return None, verification.status

    def check_verification(self, to: str, code: str) -> tuple[Exception, str]:
        verification_check = self._service.verification_checks.create(to=to, code=code)

        return None, verification_check.status
