import json
import os

import requests
from flask import request

# Hard coding this until we have proper requirements for notification service
SLACK_ENDPOINT = "https://prod-26.japaneast.logic.azure.com:443/workflows/c741150e080e4983879dda476469d593/triggers/request/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Frequest%2Frun&sv=1.0&sig=psQSQzd6DC2tzlyJcmsToPN-26Ne6zEVa9WqYka30RM"  # noqa: E501


class SlackNotificationService:
    @staticmethod
    def send():
        notification = request.args.get("notification", "true")

        env = os.environ["ENV"]
        pay_load = {
            "env": env,
        }
        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        if notification != "false":
            requests.post(SLACK_ENDPOINT, data=json.dumps(pay_load), headers=headers)
