import hmac
import json
from hashlib import sha256
from html import escape
from json import JSONDecodeError

import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def logentries_webhook(request):
    url = settings.GOOGLECHAT_LOGENTRIES_WEBHOOK_URL
    if not url:
        # Webhook non configuré (variable GOOGLECHAT_LOGENTRIES_WEBHOOK_URL)
        return HttpResponse(status=404)
    try:
        body = json.loads(request.POST.get("payload"))
        if "alert" not in body:
            return HttpResponse(status=400)
        r = requests.post(url, json=generate_json_from_issue(body), timeout=10)
        return HttpResponse(status=r.status_code, content=r.text)
    except Exception:
        return HttpResponse(status=400, content="Bad request")


def generate_json_from_issue(body):
    obj = {
        "cards": [
            {
                "sections": [
                    {
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": f"<b>Event :</b> {escape(body['event']['m'])}<br/>"
                                    f"<b>Timestamp :</b> {body['event']['t']}<br/>"
                                }
                            },
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Open Logentries",
                                            "onClick": {
                                                "openLink": {
                                                    "url": settings.LOGENTRIES_URL
                                                },
                                            },
                                        }
                                    }
                                ]
                            },
                        ],
                    }
                ],
                "header": {
                    "title": f"New alert : {body['alert']['name']}",
                    "subtitle": f"{body['log']['name']}",
                    "imageUrl": "https://cdn.betterttv.net/emote/5e0fa9d40550d42106b8a489/3x",
                    "imageStyle": "AVATAR",
                },
            }
        ]
    }
    return obj
