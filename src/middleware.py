import firebase_admin
import logging
import re
from firebase_admin import auth
from functools import wraps
from flask import request, Response
from typing import Any, Callable


default_app = firebase_admin.initialize_app()
log = logging.getLogger(__name__)


def jwt_authenticated():
    """Decorator function to authenticate the user."""

    def decorator(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            header = request.headers.get("Authorization", None)
            if header:
                token = header.split(" ")[1]
                try:
                    decoded_token = auth.verify_id_token(token)
                except Exception as e:
                    log.error(e)
                    return Response(
                        status=403, response=f"Error with authentication: {e}"
                    )
            else:
                return Response(status=401)

            request.claims = decoded_token
            return func(*args, **kwargs)

        return wrapper

    return decorator


def jwt_authorized(scope: str):
    """Decorator function to authorize the user.
    Should be use after @jwt_authenticated() to obtain the custom claims

    :param scope: the minimum scope required to access the resource
    :type scope: str
    """

    def decorator(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:

            # request.claims acquired from authentication
            claims = request.claims
            claims_role = claims["role"]
            claims_role_id = claims["role_id"]

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

            # Below logic is the basic authorization for patients/doctors
            # related. This should be factored into a different method
            # Write it here just for demonstration purpose
            if scope_role == "Patient":

                # Bypass all patients access for doctor
                if claims_role == "Doctor":
                    return func(*args, **kwargs)

                if claims_role == "Patient" and claims_role_id == scope_role_id:
                    return func(*args, **kwargs)

            return Response(
                status=401, response="User not authorized to perform given action"
            )

        return wrapper

    return decorator
