import hmac
import json
from hashlib import sha256
from unittest import mock

import requests
from django.test import SimpleTestCase, override_settings

SECRET = "test-sentry-secret"
CHAT_URL = "https://chat.example.test/hook"

ISSUE = {
    "action": "created",
    "data": {
        "issue": {
            "id": "1", "title": "Boom", "culprit": "x", "firstSeen": "a",
            "lastSeen": "b", "platform": "python", "shortId": "MIX-1",
        }
    },
}


def signed(body_bytes, secret=SECRET):
    return hmac.new(secret.encode(), body_bytes, sha256).hexdigest()


@override_settings(SENTRY_CLIENT_SECRET=SECRET, GOOGLECHAT_WEBHOOK_URL=CHAT_URL)
class SentryWebhookTest(SimpleTestCase):
    url = "/sentry-webhook/"

    def post(self, payload, signature=None, raw=None):
        body = raw if raw is not None else json.dumps(payload).encode()
        headers = {}
        if signature is not False:
            headers["HTTP_SENTRY_HOOK_SIGNATURE"] = signed(body) if signature is None else signature
        return self.client.post(self.url, data=body, content_type="application/json", **headers)

    def test_valid_signature_forwards_to_chat_with_a_timeout(self):
        with mock.patch("requests.post") as post:
            post.return_value = mock.Mock(status_code=200, text="ok")
            response = self.post(ISSUE)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_args.kwargs["timeout"], 10)
        self.assertEqual(post.call_args.args[0], CHAT_URL)

    def test_wrong_or_missing_signature_is_refused(self):
        with mock.patch("requests.post") as post:
            self.assertEqual(self.post(ISSUE, signature="0" * 64).status_code, 400)
            self.assertEqual(self.post(ISSUE, signature=False).status_code, 400)
            self.assertEqual(self.post(ISSUE, signature="é-non-ascii").status_code, 400)
        post.assert_not_called()

    def test_invalid_json_with_valid_signature_gives_400_not_500(self):
        self.assertEqual(self.post(None, raw=b"{pas du json").status_code, 400)

    def test_payload_without_issue_is_refused(self):
        self.assertEqual(self.post({"action": "x", "data": {}}).status_code, 400)
        self.assertEqual(self.post({"action": "x"}).status_code, 400)

    def test_chat_unreachable_gives_502(self):
        with mock.patch("requests.post", side_effect=requests.ConnectionError):
            self.assertEqual(self.post(ISSUE).status_code, 502)

    @override_settings(SENTRY_CLIENT_SECRET="")
    def test_missing_secret_gives_404_not_500(self):
        self.assertEqual(self.post(ISSUE, signature="x").status_code, 404)

    @override_settings(GOOGLECHAT_WEBHOOK_URL="")
    def test_missing_chat_url_gives_404(self):
        self.assertEqual(self.post(ISSUE).status_code, 404)


class LogentriesWebhookTest(SimpleTestCase):
    url = "/logentries-webhook/"

    @override_settings(GOOGLECHAT_LOGENTRIES_WEBHOOK_URL="")
    def test_not_configured_gives_404_and_calls_nothing(self):
        with mock.patch("requests.post") as post:
            response = self.client.post(self.url, {"payload": json.dumps({"alert": {}})})
        self.assertEqual(response.status_code, 404)
        post.assert_not_called()

    @override_settings(GOOGLECHAT_LOGENTRIES_WEBHOOK_URL=CHAT_URL)
    def test_forwarding_uses_a_timeout(self):
        payload = {"alert": {"name": "a"}, "log": {"name": "l"}, "event": {"m": "msg", "t": 1}}
        with mock.patch("requests.post") as post:
            post.return_value = mock.Mock(status_code=200, text="ok")
            response = self.client.post(self.url, {"payload": json.dumps(payload)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.call_args.kwargs["timeout"], 10)
