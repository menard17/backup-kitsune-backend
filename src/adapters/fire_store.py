from firebase_admin import firestore


class FireStoreClient:
    def __init__(self, client: firestore._FirestoreClient = None):
        self.client = client or firestore.client()

    def update_value(self, collection: str, collection_id: str, value: dict):
        ref = self.client.collection(collection).document(collection_id)
        ref.update(value)

    def add_value(self, collection: str, value: dict, id: str = ""):
        if id == "":
            self.client.collection(collection).add(value)
        else:
            self.client.collection(collection).document(id).set(value)

    def get_collection(self, collection: str):
        return self.client.collection(collection)
