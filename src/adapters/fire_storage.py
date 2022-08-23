import json
import os
import urllib.parse

import pandas as pd
from google.cloud import storage

BASE_STORAGE_URL = os.getenv("GCP_STORAGE_BASE_PATH")


class StorageClient:
    def upload_blob_from_memory(self, output, bucket_name, object_name, file_name):
        """Uploads a file to the bucket."""
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"{object_name}/{file_name}")
        encoded_blob_path = urllib.parse.quote(f"{object_name}/{file_name}", safe="")
        df = pd.read_json(json.dumps(output))
        blob.upload_from_string(data=df.to_csv(), content_type="text/csv")
        return f"{BASE_STORAGE_URL}/b/{bucket_name}/o/{encoded_blob_path}"
