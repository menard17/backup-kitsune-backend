import logging
import re
from functools import wraps
from typing import Any, Callable

import firebase_admin
from firebase_admin import auth as firebase_auth
from flask import Response, request

from utils import role_auth

default_app = firebase_admin.initialize_app()
log = logging.getLogger(__name__)


def jwt_authenticated(email_validation: bool = False):
    """Decorator function to authenticate the user.

    email_validation is not in authorizations because this needs to be validated before role is created.

    :param email_validation: Additional authorizations to check if email is from allow list or not
    :type email_validation: bool
    """

    def decorator(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            header = request.headers.get("Authorization", None)
            if header:
                token = header.split(" ")[1]
                try:
                    decoded_token = firebase_auth.verify_id_token(token)
                except Exception as e:
                    log.error(e)
                    return Response(
                        status=403, response=f"Error with authentication: {e}"
                    )
            else:
                return Response(status=401)

            if not decoded_token.get("email_verified"):
                return Response(status=401)

            if email_validation:
                allowed_list = ["umed.jp", "inhome.co.jp", "fake.umed.jp"]
                email = decoded_token.get("email")
                if email.split("@")[1] not in allowed_list:
                    return Response(status=401)

            request.claims = decoded_token
            return func(*args, **kwargs)

        return wrapper

    return decorator


def jwt_authorized(scope: str):
    """Decorator function to authorize the user.
    Should be use after @jwt_authenticated() to obtain the custom claims

    The decorator usage is as below:
    ```
    @jwt_authorized("/role/role_id")
    def function(role_id: str):
        ...
    ```
    in which "role" and *roleId" combination defines the scope - minimum
    permission required for the caller to access the above function.

    Below are some examples:

    * @jwt_authorized("/Patient/{patient_id}"): the caller need to have access
    to Patient resource with patient_id
    * @jwt_authorized("/Patient/*"): the caller need to have access to all
    Patients resource

    :param scope: the minimum scope required to access the resource
    :type scope: str
    """

    def decorator(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # This would produce the formatted scope with role and roleId
            # e.g. if scope is "/Patient/{patient_id}" and patient_id is 123
            # then the result is "/Patient/123"
            formatted_scope = scope.format_map(kwargs)

            # Then use regex to extract the "role" and "role_id" from the
            # formatted_scope using Named Groups
            scope_dict = re.match(
                r"^\/(?P<role>[^\/]+)\/(?P<role_id>[^\/]+)$", formatted_scope
            ).groupdict()

            scope_role = scope_dict["role"]
            scope_role_id = scope_dict["role_id"]

            # request.claims acquired from authentication
            claims_roles = role_auth.extract_roles(request.claims)
            if role_auth.is_authorized(claims_roles, scope_role, scope_role_id):
                return func(*args, **kwargs)

            return Response(
                status=401, response="User not authorized to perform given action"
            )

        return wrapper

    return decorator
