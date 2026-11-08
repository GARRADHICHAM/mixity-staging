from django.contrib.auth.mixins import AccessMixin
from django.test import SimpleTestCase
from django.urls import get_resolver
from django.views import View


def routed_view_classes():
    classes = {}

    def walk(patterns):
        for pattern in patterns:
            if hasattr(pattern, "url_patterns"):
                walk(pattern.url_patterns)
                continue
            callback = pattern.callback
            cls = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
            if isinstance(cls, type):
                classes[cls] = str(pattern.pattern)

    walk(get_resolver().url_patterns)
    return classes


class ViewProtectionTest(SimpleTestCase):
    def test_access_mixins_come_before_the_base_view(self):
        """
        `class X(TemplateView, LoginRequiredMixin)` ne protège rien : la vue de base traite la
        requête sans jamais appeler le mixin. Le mixin doit être placé AVANT la vue de base.
        """
        misplaced = [
            f"{cls.__module__}.{cls.__name__} ({url})"
            for cls, url in routed_view_classes().items()
            if AccessMixin in cls.__mro__
            and View in cls.__mro__
            and cls.__mro__.index(AccessMixin) > cls.__mro__.index(View)
        ]
        self.assertEqual(misplaced, [])
