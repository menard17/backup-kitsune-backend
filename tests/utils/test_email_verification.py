from utils.email_verification import is_email_in_allowed_list, is_email_verified


class MockRequest:
    def __init__(self, email, verified=True):
        self.claims = {"email": email, "email_verified": verified}


def test_not_verify_email():
    mock_request = MockRequest("test@fakes.umed.jp")
    assert not is_email_in_allowed_list(mock_request)


def test_verify_email_and_email_verified():
    mock_request = MockRequest("test@umed.jp")
    assert is_email_in_allowed_list(mock_request)
    assert is_email_verified(mock_request)


def test_verify_email_with_addon():
    mock_request = MockRequest("test@fakes.umed.jp")
    assert is_email_in_allowed_list(mock_request, "fakes.umed.jp")


def test_email_not_verified():
    mock_request = MockRequest("test@umed.jp", False)
    assert not is_email_verified(mock_request)
