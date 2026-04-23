import hmac
import json
from hashlib import sha256

import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def sentry_webhook(request):
    expected = hmac.new(
        key=settings.SENTRY_CLIENT_SECRET.encode("utf-8"),
        msg=request.body,
        digestmod=sha256,
    ).hexdigest()
    body = json.loads(request.body)

    if (
        "Sentry-Hook-Signature" not in request.headers
        or expected != request.headers["Sentry-Hook-Signature"]
    ):
        return HttpResponse(status=400)
    url = settings.GOOGLECHAT_WEBHOOK_URL
    if "issue" not in body["data"]:
        return HttpResponse(status=400)
    r = requests.post(url, json=generate_json_from_issue(body))
    return HttpResponse(status=r.status_code, content=r.text)


def generate_json_from_issue(body):
    issue = body["data"]["issue"]
    if body["action"] == "resolved":
        picture = "https://i.kym-cdn.com/photos/images/newsfeed/001/734/410/676.jpg"
    elif body["action"] == "assigned":
        picture = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSgYgKOLfFelNWKpF3j3Zy-PcyyCHxoTSq00roSrDMn5A&s"
    else:
        picture = "https://cdn.betterttv.net/emote/5f4f4fa23769246c0320de37/3x"
    obj = {
        "cards": [
            {
                "sections": [
                    {
                        "widgets": [
                            {
                                "textParagraph": {
                                    "text": f"<b>Exception :</b> {issue['title']}<br/>"
                                    f"<b>Culprit :</b> {issue['culprit']}<br/>"
                                    f"<b>First Seen :</b> {issue['firstSeen']}<br/>"
                                    f"<b>Last Seen :</b> {issue['lastSeen']}<br/>"
                                    f"<b>Platform :</b> {issue['platform']} / {issue['shortId']}<br/>"
                                }
                            },
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "Open Sentry",
                                            "onClick": {
                                                "openLink": {
                                                    "url": f"https://sentry.io/organizations/mixity-company/issues/{issue['id']}/"
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
                    "title": f"Issue {body['action']}",
                    "subtitle": f"#{issue['id']}",
                    "imageUrl": picture,
                    "imageStyle": "AVATAR",
                },
            }
        ]
    }
    return obj
