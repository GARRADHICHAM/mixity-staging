from types import SimpleNamespace
from unittest import mock

from django.test import RequestFactory, SimpleTestCase

from scoring.mails import alert_evaluation_created_mail


def evaluation(subscription):
    structure = SimpleNamespace(workforce=250)
    return SimpleNamespace(
        id=940,
        subscription=subscription,
        sheet=SimpleNamespace(type=SimpleNamespace(name="Evaluation Mixity Diag")),
        entity=SimpleNamespace(entity_level=SimpleNamespace(structure=structure)),
    )


class AlertEvaluationCreatedMailTest(SimpleTestCase):
    def send(self, ev):
        request = RequestFactory().get("/")
        with mock.patch("scoring.mails.render_to_string", return_value="") as render, mock.patch(
            "scoring.mails.send"
        ) as send:
            alert_evaluation_created_mail("user", request, ev)
        send.assert_called_once()
        return render.call_args.args[1]

    def test_evaluation_without_subscription_does_not_crash(self):
        context = self.send(evaluation(None))
        self.assertEqual(context["subscription_type"], "Evaluation Mixity Diag")

    def test_evaluation_with_subscription_keeps_its_type(self):
        context = self.send(evaluation(SimpleNamespace(subscription_type="Pack 360")))
        self.assertEqual(context["subscription_type"], "Pack 360")
