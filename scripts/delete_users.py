from firebase_admin import auth


def delete_all_users():
    for user in auth.list_users().iterate_all():
        auth.delete_user(user.uid)
