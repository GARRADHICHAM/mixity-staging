import datetime
from unittest import mock

import stripe
from django.test import TestCase

from payments.models import CheckoutSession

URL = "/payments/webhook/"


def event(kind="checkout.session.completed", **obj):
    obj.setdefault("object", "checkout.session")
    return {"type": kind, "data": {"object": obj}}


class StripeWebhookTest(TestCase):
    def post(self, ev=None, signature="t=1,v1=x", raise_error=None):
        headers = {"HTTP_STRIPE_SIGNATURE": signature} if signature else {}
        with mock.patch("stripe.Webhook.construct_event", return_value=ev, side_effect=raise_error):
            return self.client.post(URL, data="{}", content_type="application/json", **headers)

    def test_only_post_is_accepted(self):
        self.assertEqual(self.client.get(URL).status_code, 405)

    def test_missing_signature_header_gives_400_not_500(self):
        self.assertEqual(self.post(event(id="cs_1"), signature=None).status_code, 400)

    def test_invalid_signature_gives_400(self):
        error = stripe.error.SignatureVerificationError("bad", "sig")
        self.assertEqual(self.post(raise_error=error).status_code, 400)

    def test_unknown_session_gives_200_so_stripe_stops_retrying(self):
        self.assertEqual(self.post(event(id="cs_unknown")).status_code, 200)
        self.assertEqual(
            self.post(event("payment_intent.succeeded", object="payment_intent", id="pi_unknown")).status_code, 200
        )

    def test_session_without_subscription_gives_200_and_activates_nothing(self):
        CheckoutSession.objects.create(
            checkout_id="cs_known", payment_intent="pi_known", payment_status="",
            expires_at=datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc),
        )
        response = self.post(event(id="cs_known", payment_intent="pi_known", payment_status="paid"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CheckoutSession.objects.get(checkout_id="cs_known").payment_status, "")
