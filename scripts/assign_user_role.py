import firebase_admin
from firebase_admin import auth


def assign_staff_role(email: str):
    _ = firebase_admin.initialize_app()

    user = auth.get_user_by_email(email)
    custom_claims = user.custom_claims or {}

    current_roles = custom_claims.get("roles", {})
    current_roles["Staff"] = {}
    auth.set_custom_user_claims(user.uid, {"roles": current_roles})


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser("assign_role_parser")
    parser.add_argument("email", help="Email to assign staff role", type=str)
    args = parser.parse_args()
    assign_staff_role(args.email)
