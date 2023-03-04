from utils.logging import add_gcp_fields


def test_add_gcp_fields():
    event_dict = {
        "level": "info",
        "event": "sample-message",
        "timestamp": "2023-03-04T13:37:31.098869Z",
        "extra": "sample-extra-field",
    }

    add_gcp_fields(None, None, event_dict)

    assert event_dict == {
        "severity": "info",
        "message": "sample-message",
        "time": "2023-03-04T13:37:31.098869Z",
        "extra": "sample-extra-field",
    }
