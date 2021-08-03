import requests
import json
import os

from firebase_admin import auth

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

def get_token(uid):
    """Return a Firebase ID token dict from a user id (UID).
    Returns:
    dict: Keys are "kind", "idToken", "refreshToken", and "expiresIn".
    "expiresIn" is in seconds.
    The return dict matches the response payload described in
    https://firebase.google.com/docs/reference/rest/auth/#section-verify-custom-token
    The actual token is at get_token(uid)["idToken"].
    """
    token = auth.create_custom_token(uid)
    data = {
        'token': token.decode('utf-8'),
        'returnSecureToken': True
    }

    url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key={FIREBASE_API_KEY}"

    resp = requests.post(
        url,
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )

    return resp.json()["idToken"]
