import json
import os

import requests

EMAIL_ENDPOINT = "https://prod-12.japaneast.logic.azure.com:443/workflows/eed426b21f80447ba3e99911c55bd4e3/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Astj0_07szoJ6YYnfoeEN_kVyLNmOVefNwD0aogXvS8"  # noqa: E501


class EmailNotificationService:
    @staticmethod
    def send():
        env = os.environ["ENV"]
        pay_load = {"env": env}
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        requests.post(EMAIL_ENDPOINT, data=json.dumps(pay_load), headers=headers)
