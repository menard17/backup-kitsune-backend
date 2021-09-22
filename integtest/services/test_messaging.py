import os

import pytest

from services.messaging_service import MessagingController


def test_send_push_notification(test_message_data):
    response = MessagingController(dry_run=True).send_push_notification(
        test_message_data
    )
    assert response.status_code == 200


@pytest.fixture
def test_message_data():
    yield {
        "title": "Test Notification Title",
        "body": "Test Notification Body",
        "fcm_token": os.environ.get("FCM_TOKEN"),
    }
