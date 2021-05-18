from functools import wraps
from typing import Any, Callable, Dict

import firebase_admin
from firebase_admin import auth  # noqa: F401
from flask import request, Response
import logging


default_app = firebase_admin.initialize_app()
log = logging.getLogger(__name__)


# [START cloudrun_user_auth_jwt]
def jwt_authenticated(func: Callable[..., int]) -> Callable[..., int]:
    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:

        header = request.headers.get("Authorization", None)
        if header:
            token = header.split(" ")[1]
            try:
                decoded_token = firebase_admin.auth.verify_id_token(token)
            except Exception as e:
                log.error(e)
                return Response(status=403, response=f"Error with authentication: {e}")
        else:
            return Response(status=401)

        request.uid = decoded_token["uid"]
        return func(*args, **kwargs)

    return decorated_function


# [END cloudrun_user_auth_jwt]