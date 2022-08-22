from firebase_admin import firestore


class FireStoreClient:
    def update_value(self, collection: str, collection_id: str, value: dict):
        db = firestore.client()
        ref = db.collection(collection).document(collection_id)
        ref.update(value)
