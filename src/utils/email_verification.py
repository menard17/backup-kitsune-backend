from flask import request


def is_email_verified(request: request) -> bool:
    """Returns true if email is verified

    :param request: reqeust from jwt_token
    :type request: request
    """
    return "email_verified" not in request.claims or bool(
        request.claims["email_verified"]
    )


def is_email_in_allowed_list(request: request, addon_email=str) -> bool:
    """Returns true if domain of email is in allowed_list

    :param request: reqeust from jwt_token
    :type request: request
    """
    allowed_list = ["umed.jp", "inhome.co.jp", "fake.umed.jp"]
    allowed_list.append(addon_email)
    return (
        "email" in request.claims
        and request.claims["email"].split("@")[1] in allowed_list
    )
