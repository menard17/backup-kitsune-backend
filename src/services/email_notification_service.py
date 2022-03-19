import json
import os
from datetime import datetime
from typing import Dict

import requests

EMAIL_ENDPOINT = "https://prod-25.northcentralus.logic.azure.com:443/workflows/108894277fde4e4ea6d5894e8bd05b5a/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=kP-CxO9SUX6sDVZIh6ItOR1E4inz62owZCR7Ml8vQSo"  # noqa: E501


class EmailNotificationService:
    @staticmethod
    def send(
        start: datetime,
        end: datetime,
        patient_name: Dict,
        en_practitioner_name: Dict,
        ja_practitioner_name: Dict,
        patient_email: str,
        is_visit: bool,
        cancellation: bool,
    ):
        date_format = "%Y/%m/%d"
        time_format = "%H:%M"
        env = os.environ["ENV"]
        pay_load = {
            "env": env,
            "date": start.strftime(date_format),
            "start": start.strftime(time_format),
            "end": end.strftime(time_format),
            "patient_name": str(patient_name),
            "patient_family_name": patient_name["family"],
            "patient_email": patient_email,
            "is_visit": str(is_visit),
            "cancellation": str(cancellation),
        }

        if en_practitioner_name:
            pay_load["en_practitioner_family"] = en_practitioner_name["family"]
            pay_load["en_practitioner_given"] = en_practitioner_name["given"][0]
        if ja_practitioner_name:
            pay_load["ja_practitioner_family"] = ja_practitioner_name["family"]
            pay_load["ja_practitioner_given"] = ja_practitioner_name["given"][0]
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        requests.post(EMAIL_ENDPOINT, data=json.dumps(pay_load), headers=headers)
