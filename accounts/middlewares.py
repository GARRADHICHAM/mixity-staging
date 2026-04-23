from django.shortcuts import redirect, reverse
from mixity.utils import encryption
from urllib.parse import quote_plus

from accounts.models import (
    Structure,
)


class UserCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def check_all_possible_url(self, request):
        encryption_class = encryption()
        encrypted_email = quote_plus(encryption_class.encrypt_data(request.user.email))
        encrypted_email = encrypted_email.replace("%2F", "%252F")
        structures = Structure.objects.filter(members=request.user)

        for structure in structures:
            if (
                reverse(
                    "dashboard:account:collaborator_evaluation_redirect",
                    kwargs={
                        "slug": structure.slug,
                        "encrypted_email": encrypted_email,
                    },
                )
                == request.path
            ):
                return True
        return False

    def __call__(self, request):
        # this is used to force user to complete the onboarding

        # is_confirmed => user has confirmed his email
        # is_qualified => user has filled first_name and last_name
        if request.user and request.user.is_authenticated:
            if request.user.is_confirmed and not request.user.is_qualified:
                if (
                    reverse("dashboard:account:dashboard_register_confirmed")
                    != request.path
                    and self.check_all_possible_url(request)
                    and reverse("user:logout") != request.path
                    and reverse("javascript-catalog") != request.path
                ):
                    return redirect("dashboard:account:dashboard_register_confirmed")
        response = self.get_response(request)
        # Code to be executed for each request/response after
        # the view is called.
        return response
