from datetime import (
    datetime,
    date,
)
import responses
import stripe
from django.conf import settings
from mixity.testing import TestCase

# Create your tests here.
from django.utils import timezone
from django.utils.timezone import make_aware

from accounts.models import MixityUser, Structure, Membership, BusinessLine
from payments.models import CheckoutSession
from payments.views import stripe_config, StructureCreateCheckoutSession, stripe_webhook
from scoring.models import QuestionSheetType
from subscriptions.models import SubscriptionType, Subscription
from django.test import RequestFactory
from django.core import mail

event_type = None
payment_status = None
status = None
discount = None


def create_event(*args, **kwargs):
    return {
        "id": "my_event_id",
        "object": "event",
        "api_version": "2020-08-27",
        "created": 1631797657,
        "data": {
            "object": {
                "id": "my_checkout_session",
                "customer": "my_customer",
                "object": "checkout.session",
                "amount_subtotal": 120000,
                "amount_total": 144000,
                "payment_status": payment_status,
                "payment_intent": "my_payment_intent",
                "status": status,
                "total_details": {
                    "amount_discount": discount or 0,
                },
            }
        },
        "type": event_type,
    }


# class PaymentTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super(PaymentTest, cls).setUpClass()
#         # Categories
#         cls.make_categories()

#         sheet_type = QuestionSheetType.objects.create(
#             slug="mixity_start",
#             name="Sheet Type",
#         )
#         # BusinessLine
#         slug = "others"
#         name_fr = "Autre - précisez"
#         name_en = "Others"
#         businessLine = cls.make_business_line(slug,name_fr,name_en)

#         # Structure
#         juridic_name="My Structure"
#         slug="my_structure"
#         workforce=100
#         category="Diversity"
#         s = cls.make_structure(juridic_name,slug,workforce,category,businessLine)
#         e_lvl_0 = cls.make_entity_level(s, "Groupe", 0)
#         e = cls.make_entity(s.juridic_name, e_lvl_0, s.workforce)
#         # User
#         u = cls.make_common_user()
#         # Subscription Type
#         label="Mixity Start"
#         pme_label="Mixity Start"
#         slug="mixity_start"
#         order=4
#         desc="L'évaluation instantanée pour débuter votre politique de diversité et inclusion"
#         sub = cls.make_subscription_type(label,pme_label,slug,order,desc,True)

#         # Subscription
#         sb = cls.make_subscription(sheet_type,sub,s,False)
#         sub_pack = cls.make_subscription_pack(date.today(), s)
#         product = cls.make_product(label, slug, sheet_type)
#         sub_opt = cls.make_subscription_option(sub_pack, product.slug)

#         # Membership
#         cls.make_membership(u,s)
#         cls.make_entity_membership(u, e)

#         # Price.objects.create(
#         #     tax_free_price=500, subscription_type=sub, stripe_price_id="not_empty"
#         # )
#         # Attributes
#         cls.user = u
#         cls.structure = s
#         cls.subscription = sb
#         cls.subscription_type = sub

#     # def test_can_pay_by_card(self):
#     #     self.assertTrue(self.structure.can_pay_by_card)

#     def test_cant_pay_by_card(self):
#         self.subscription_type.allow_card_payment = False
#         self.subscription_type.save()
#         self.assertFalse(self.structure.can_pay_by_card)

#     # def test_cant_pay_by_card_no_price(self):
#     #     self.subscription_type.prices.update(stripe_price_id="")
#     #     self.assertFalse(self.structure.can_pay_by_card)

#     # @responses.activate
#     # def test_create_checkout_session(self):
#     #     responses.add(
#     #         responses.POST,
#     #         "https://api.stripe.com/v1/checkout/sessions",
#     #         json={
#     #             "id": "my_checkout_session",
#     #             "payment_intent": "my_payment_intent",
#     #             "expires_at": datetime.timestamp(datetime.now()) + 86400,
#     #         },
#     #         status=200,
#     #     )
#     #     factory = RequestFactory()
#     #     request = factory.get(
#     #         f"",
#     #     )
#     #     request.META["HTTP_HOST"] = "0.0.0.0:8000"
#     #     request.user = self.user
#     #     StructureCreateCheckoutSession.as_view()(request, pk=self.structure.id)
#     #     checkout_session = CheckoutSession.objects.first()

#     #     # check if correct info in checkout session object
#     #     self.assertEqual("my_checkout_session", checkout_session.checkout_id)
#     #     self.assertEqual("my_payment_intent", checkout_session.payment_intent)

#     #     StructureCreateCheckoutSession.as_view()(request, pk=self.structure.id)

#     #     # check if no double creation of checkoutsession
#     #     self.assertEqual(CheckoutSession.objects.count(), 1)
#     #     # check if checkout session not replaced if not expired
#     #     self.assertEqual(CheckoutSession.objects.first().id, checkout_session.id)

#     #     # we expire the checkout session
#     #     CheckoutSession.objects.update(expires_at=make_aware(datetime.fromtimestamp(0)))

#     #     StructureCreateCheckoutSession.as_view()(request, pk=self.structure.id)

#     #     # we test if the previous checkout session expiration didn't cause a double creation
#     #     self.assertEqual(CheckoutSession.objects.count(), 1)
#     #     # we check that a new checkout session has been created to replace the expired one
#     #     self.assertNotEqual(CheckoutSession.objects.first().id, checkout_session.id)

#     def create_request(self):
#         checkout = CheckoutSession.objects.get_or_create(
#             payment_intent="my_payment_intent",
#             checkout_id="checkout_id",
#             subscription=self.subscription,
#             defaults={"expires_at": timezone.now()},
#         )

#         factory = RequestFactory()
#         request = factory.get(
#             f"",
#         )
#         request.META["HTTP_HOST"] = "0.0.0.0:8000"
#         request.META[
#             "HTTP_STRIPE_SIGNATURE"
#         ] = f"t={datetime.timestamp(datetime.now())},v1=v1sig,v0=v0sig"
#         request.user = self.user

#         # we mock the create_event method to bypass stripe signature verification
#         stripe.Webhook.construct_event = create_event
#         return request

#     def email_test_cases(self):
#         # test that emails are sent to owners and to Mixity
#         self.assertEqual(len(mail.outbox), 2)
#         cases = [
#             {
#                 "emails": [self.user.email],
#                 "subject": "[MIXITY] Paiement pour votre offre Mixity reçu",
#             },
#             {
#                 "emails": [settings.MIXITY_EMAIL_FROM],
#                 "subject": "[MIXITY] Nouvelle facture Mixity disponible",
#             },
#         ]
#         for key, value in enumerate(cases):
#             self.assertEqual(mail.outbox[key].to, value["emails"])
#             self.assertEqual(mail.outbox[key].subject, value["subject"])

#     def test_discounts(self):
#         global event_type, payment_status, discount

#         event_type = "checkout.session.completed"
#         payment_status = "paid"
#         discount = 5009
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         # stripe prices are in cents. database prices are in euros (ex : 5000 from Stripe <=> 50.00 from database)
#         self.assertEqual(
#             float(self.subscription.invoice.tax_free_price), 1149.91
#         )  # tax free price = original ht price - discount
#         self.assertEqual(float(self.subscription.invoice.tax_included_price), 1440.00)
#         self.assertEqual(
#             float(self.subscription.invoice.tax), 290.09
#         )  # tax is calculated with the discounted amount
#         self.email_test_cases()

#     def test_payment_success_sync(self):
#         global event_type, payment_status

#         event_type = "checkout.session.completed"
#         payment_status = "paid"
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         self.assertTrue(self.subscription.is_active)
#         self.assertIsNotNone(self.subscription.invoice)
#         self.assertTrue(self.subscription.invoice.paid)
#         self.email_test_cases()

#     def test_payment_async_wait(self):
#         global event_type, payment_status

#         event_type = "checkout.session.completed"
#         payment_status = "unpaid"
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         self.assertFalse(self.subscription.is_active)
#         self.assertIsNotNone(self.subscription.invoice)
#         self.assertFalse(self.subscription.invoice.paid)
#         self.email_test_cases()

#     def test_payment_async_done(self):
#         global event_type, payment_status

#         event_type = "checkout.session.completed"
#         payment_status = "unpaid"
#         stripe_webhook(self.create_request())

#         event_type = "checkout.session.async_payment_succeeded"
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         self.assertTrue(self.subscription.is_active)
#         self.assertTrue(self.subscription.invoice.paid)
#         self.email_test_cases()

#     def test_payment_async_fail(self):
#         global event_type, payment_status

#         event_type = "checkout.session.completed"
#         payment_status = "unpaid"
#         stripe_webhook(self.create_request())

#         event_type = "checkout.session.async_payment_failed"
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         self.assertFalse(self.subscription.is_active)
#         self.assertFalse(self.subscription.invoice.paid)

#     def test_dispute_lost(self):
#         global event_type, payment_status, status

#         event_type = "checkout.session.completed"
#         payment_status = "paid"
#         stripe_webhook(self.create_request())

#         event_type = "charge.dispute.closed"
#         status = "lost"
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         self.assertFalse(self.subscription.is_active)
#         self.assertFalse(self.subscription.invoice.paid)

#     def test_dispute_friendly(self):
#         global event_type, payment_status, status

#         event_type = "checkout.session.completed"
#         payment_status = "paid"
#         stripe_webhook(self.create_request())

#         event_type = "charge.dispute.closed"
#         status = "not_lost_manual_refund"
#         stripe_webhook(self.create_request())
#         self.subscription.refresh_from_db()
#         self.assertTrue(self.subscription.is_active)
#         self.assertTrue(self.subscription.invoice.paid)
