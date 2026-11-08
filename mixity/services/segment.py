import base64
import json

import requests

from django.conf import settings


class SegmentAPI:
    BASE_URL = "https://api.segment.io/v1/"

    def __init__(self, api_key=None):
        if not api_key:
            api_key = settings.SEGMENT_KEY
        self.api_key = api_key

    def identify(self, user_id, traits):
        return requests.post(
            self.BASE_URL + "identify",
            data=json.dumps({"userId": user_id, "traits": traits}),
            headers=self.get_headers(),
            timeout=10,
        )

    def track(self, user_id, event, properties):
        return requests.post(
            self.BASE_URL + "track",
            data=json.dumps(
                {"userId": user_id, "event": event, "properties": properties}
            ),
            headers=self.get_headers(),
            timeout=10,
        )

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": "Basic "
            + base64.b64encode((self.api_key + ":").encode("utf-8")).decode("utf-8"),
        }
