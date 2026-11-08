from types import SimpleNamespace
from unittest import mock

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, SimpleTestCase, override_settings

from payments.views import StructurePaymentView

STRUCTURE = SimpleNamespace(is_partial=False, get_main_entity=SimpleNamespace(slug="org1-main"))


class StructurePaymentPageTest(SimpleTestCase):
    def get(self):
        request = RequestFactory().get("/payments/1/pay/")
        SessionMiddleware(lambda r: None).process_request(request)
        request._messages = FallbackStorage(request)
        with mock.patch.object(StructurePaymentView, "get_object", return_value=STRUCTURE):
            return StructurePaymentView.as_view()(request, pk=1), request

    @override_settings(STRIPE_PUBLIC_KEY="")
    def test_without_stripe_key_redirects_to_dashboard_with_message(self):
        response, request = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/org1-main/")
        self.assertEqual(len(list(request._messages)), 1)

    @override_settings(STRIPE_PUBLIC_KEY="pk_test")
    def test_with_stripe_key_keeps_payment_page(self):
        with mock.patch(
            "django.contrib.auth.mixins.UserPassesTestMixin.dispatch", return_value="payment page"
        ) as dispatch:
            response, _ = self.get()
        self.assertEqual(response, "payment page")
        dispatch.assert_called_once()
