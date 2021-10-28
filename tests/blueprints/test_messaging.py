from firebase_admin import messaging

from src.blueprints.messaging import MessagingController


class FakeMessanger:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def send(self, message: messaging.Message, dry_run: bool):
        if self.should_fail:
            raise Exception("test failing while sending message")

        self.send_called = True
        self.send_message = message
        self.send_dry_run = dry_run
        return "test response"


def test_send_push_notification():
    request_body = {
        "fcm_token": "fake",
        "title": "test title",
        "body": "test body",
    }

    messanger = FakeMessanger()

    controller = MessagingController(messanger)
    resp = controller.send_push_notification(request_body)

    expected_msg = messaging.Message(
        notification=messaging.Notification(
            title=request_body["title"],
            body=request_body["body"],
        ),
        token=request_body["fcm_token"],
    )

    assert messanger.send_called is True
    assert messanger.send_message.data == expected_msg.data
    assert not messanger.send_dry_run  # default as false

    assert resp.status_code == 200
    assert resp.data.decode() == "test response"


def test_send_push_notification_returns_400_if_without_fcm_token():
    request_body = {
        "title": "test title",
        "body": "test body",
    }

    messanger = FakeMessanger()

    controller = MessagingController(messanger)
    resp = controller.send_push_notification(request_body)

    assert resp.status_code == 400
    assert resp.data.decode() == "missing param: fcm_token"


def test_send_push_notification_returns_internal_error_if_exception():
    request_body = {
        "fcm_token": "fake",
        "title": "test title",
        "body": "test body",
    }
    messanger = FakeMessanger(should_fail=True)

    controller = MessagingController(messanger)
    resp = controller.send_push_notification(request_body)

    assert resp.status_code == 500
    assert resp.data.decode() == "test failing while sending message"
