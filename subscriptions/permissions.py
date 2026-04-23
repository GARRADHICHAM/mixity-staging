from django.contrib.auth.mixins import UserPassesTestMixin


class CanEvaluateMixin(UserPassesTestMixin):
    # Check if a user is allowed to evaluate (active evaluation and owner of structure)
    permission_denied_message = (
        "Vous n'avez pas les droits pour pouvoir remplir le questionnaire."
    )

    def test_func(self):
        return self.request.user.allow_evaluation(
            self.get_subscription_option().subscriptionPack
        )
