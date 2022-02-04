from firebase_admin import auth


def grant_role(request_claims: dict, role: str, role_id: str = None):
    """Grant a role to a specific customer.

    This role is used for authorization purposes.

    A user can have multiple roles, and they are defined inside a map, with key
    as the "role type", and depends on the role, the underlying structure will
    be different. For example "Patient" and "Practitioner" has an "id" field
    indicating the FHIR resourceId, whilst "Admin" role doesn't have such "id".

    Roles live in Firebase's custom claims, under "roles" key. See this article
    https://firebase.google.com/docs/auth/admin/custom-claims

    Below are all the supported role types and the underlying structure:
    {
        "Patient": {
            "id": "patient-id"
        },
        "Practitioner": {
            "id": "practitioner-id"
        },
        "Admin": {}
    }
    """
    current_roles = extract_roles(request_claims)
    if current_roles is None:
        current_roles = {}
    if role_id is not None:
        current_roles[role] = {"id": role_id}
    else:
        current_roles[role] = {}
    uid = request_claims["uid"]
    auth.set_custom_user_claims(uid, {"roles": current_roles})


def extract_roles(request_claims: dict):
    roles = request_claims.get("roles")
    if roles is None:
        # if request_claims does not contain roles, needs to check firebase with uid
        uid = request_claims.get("uid")
        if (uid is not None) and (custom_claims := auth.get_user(uid).custom_claims):
            return custom_claims.get("roles")
    return roles


def is_authorized(claims_roles: dict, scope_role: str, scope_role_id: str) -> bool:
    """Determine if a user claims (identity from Firebase) have access to the
    defined scope.

    For now, Doctor has access to all Patients resource, and Patient has access
    to his/her own resources.

    Admin should have access to all resources.

    :param claims_roles: a dictionary describe all the roles this user has,
    extracted from firebase's custom claims.
    :type claims_roles: dict
    :param scope_role_id: the scope to determine access, e.g. Patient/Doctor
    :type scope_role: str
    :param scope_role_id: the ID for the above scope ("*" means ALL)
    :type scope_role_id: str

    :rtype: bool
    """
    # Nothing to authorize
    if claims_roles is None:
        return False

    # Admin are fully-authorized by default
    if "Admin" in claims_roles:
        return True

    if scope_role == "Patient":
        # Bypass all patients access for Practitioner (Doctor/Nurse)
        if "Practitioner" in claims_roles:
            return True

        if "Patient" in claims_roles and claims_roles["Patient"]["id"] == scope_role_id:
            return True

    if scope_role == "Practitioner":
        if (
            "Practitioner" in claims_roles
            and claims_roles["Practitioner"]["id"] == scope_role_id
        ):
            return True

    return False
