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

    The decorator usage is as below:
    ```
    @jwt_authorized("/role/role_id}")
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

    Please note that permission relationship are defined inside this decorator
    as well. For now, Doctor has access to all Patients resource, and Patient
    has access to his/her own resources. It should be managed in a different
    function and unit tested.

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

            if is_authorized(claims_role, claims_role_id, scope_role, scope_role_id):
                return func(*args, **kwargs)

            return Response(
                status=401, response="User not authorized to perform given action"
            )

        return wrapper

    return decorator


def is_authorized(
    claims_role: str, claims_role_id: str, scope_role: str, scope_role_id: str
) -> bool:
    """Determine if a user claims (identity from Firebase) have access to the
    defined scope.

    :param claims_role: the role identity of user, e.g. Patient/Doctor
    :type claims_role: str
    :param claims_role_id: the ID for the claims_role
    :type claims_role_id: str
    :param scope_role_id: the scope to determine access, e.g. Patient/Doctor
    :type scope_role: str
    :param scope_role_id: the ID for the above scope ("*" means ALL)
    :type scope_role_id: str
    """
    if scope_role == "Patient":
        # Bypass all patients access for doctor
        if claims_role == "Practitioner":
            return True

        if claims_role == "Patient" and claims_role_id == scope_role_id:
            return True

    return False
