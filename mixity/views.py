import json

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView
from django.views.generic.base import TemplateResponseMixin, View
from mixity.models import (
    FAQCategory,
    NonEvaluatedClient,
)
from accounts.models import Entity
from mixity.services.namsor.api import Namsor

from subscriptions.models import SubscriptionPack
import logging
from django.conf import settings

from openai import OpenAI

# Translations imports
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


class OpenAIApiView(UserPassesTestMixin, LoginRequiredMixin, View):
    """
    Endpoit to use the ChatGPT API (see /static/admin/admin.js)
    """

    def post(self, request, *args, **kwargs):
        if not settings.OPEN_AI_API_KEY:
            return JsonResponse({"message": "Missing API KEY"}, status=400)
        client = OpenAI(
            api_key=settings.OPEN_AI_API_KEY,
        )
        params = json.loads(request.body.decode("utf-8"))
        text = params.get('text', '')
        target_lang = params.get('target_lang', '')
        source_lang = params.get('source_lang', '')
        system_prompt = f"You will be provided with a text or a word in {source_lang}, and your task is to translate it into {target_lang}. You must respect these next rules: be fast; only respond with the translated text; if you hesitate choose the most professional translation; if a given word is in upper-case and between curly brackets leave it as it is."
        user_prompt = text
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                { "role": "system", "content": system_prompt},
                { "role": "user", "content": user_prompt},
            ],
            temperature=0,
            top_p=0
        )
        result = response.choices[0].message.content
        return JsonResponse({"text": result})
    
    def test_func(self):
        # Endpoint has to be enabled for staff-only (to prevent unwanted usage)
        return self.request.user.is_staff


class NamsorApiUsageView(UserPassesTestMixin, LoginRequiredMixin, View):
    """
    Endpoint to retrieve API Usage of Namsor
    """

    def get(self, request, *args, **kwargs):
        return JsonResponse(Namsor.get_instance().get_usage())

    def test_func(self):
        return self.request.user.is_staff


class AmbassadorsMixin(TemplateResponseMixin):
    def get_context_data(self, **kwargs):
        context = super(AmbassadorsMixin, self).get_context_data(**kwargs)
        context["ambassadors"] = [
            {
                "name": "Anthony Babkine",
                "link": "https://twitter.com/AnthonyBabkine",
                "link_content": "@AnthonyBabkine",
                "status": _(
                    "Entrepreneur Social - Président et cofondateur Diversidays"
                ),
                "picture": "img/ambassadors/anthony_babkine.jpg",
            },
            {
                "name": "Merete Buljo",
                "link": "https://twitter.com/meretebuljo",
                "link_content": "@meretebuljo",
                "status": _("Présidente des Digital Ladies et Alliés"),
                "picture": "img/ambassadors/merete_buljo.jpg",
            },
            {
                "name": "Marion Darrieutort",
                "link": "https://twitter.com/Darrieu",
                "link_content": "@Darrieu",
                "status": _("Co-Présidente d’Entreprise et Progrès"),
                "picture": "img/ambassadors/marion_darrieutort.jpeg",
            },
            {
                "name": "Alexandra Guigand",
                "link": "https://twitter.com/passerlavague",
                "link_content": "@passerlavague",
                "status": _("Auteure - Experte handicap"),
                "picture": "img/ambassadors/alexandra_guigand.jpg",
            },
            {
                "name": "Pierre Meisel",
                "link": "https://twitter.com/PierreMeisel",
                "link_content": "@PierreMeisel",
                "status": _(
                    "Formateur et conférencier D&I - Fondateur de Team Jolokia"
                ),
                "picture": "img/ambassadors/pierre_meisel.jpg",
            },
            {
                "name": "Diariata N'Diaye",
                "link": "https://twitter.com/DiataResonantes",
                "link_content": "@DiataResonantes",
                "status": _("Entrepreuneuse - Fondatrice Résonantes & App-Elles"),
                "picture": "img/ambassadors/diariata_ndiaye_2.jpg",
            },
            {
                "name": "Samuel Tamba",
                "link": "https://twitter.com/_samueltamba",
                "link_content": "@_samueltamba",
                "status": _("Responsable des Partenariats chez LinkedIn France"),
                "picture": "img/ambassadors/samuel_tamba.jpeg",
            },
            {
                "name": "Madi Seydi",
                "link": "https://twitter.com/MadiSeydi",
                "link_content": "@MadiSeydi",
                "status": _("Directrice Conseil : Communication - Influence"),
                "picture": "img/ambassadors/madi_seydi.jpeg",
            },
        ]
        return context


class ClientMixin(TemplateResponseMixin):
    @classmethod
    def get_subscription_pack_unordered(cls):
        return (
            SubscriptionPack.active_objects.select_related("structure")
            .exclude(structure__juridic_name__in=["AFMD", "Bruce"])
            .exclude(structure__display_on_website=False)
        )

    @classmethod
    def get_subscription_pack(cls):
        return (
            cls.get_subscription_pack_unordered()
            .distinct("structure__juridic_name")
            .order_by("structure__juridic_name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription_pack = self.get_subscription_pack()
        context["companies"] = (
            Entity.objects.filter(evaluations__is_validated_by_user=True)
            .distinct("entity_level__structure")
            .count()
        )
        context["clients"] = []
        for subscription in subscription_pack:
            if subscription.structure.has_logo():
                context["clients"].append(subscription_pack[0].structure)

        for client in NonEvaluatedClient.objects.all():
            if client.has_logo:
                context["clients"].append(client)
        return context


class FAQPageView(ListView):
    model = FAQCategory
    template_name = "faq.html"


class GoogleSheetsDataCheckView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "google_sheets_data_check.html"

    def test_func(self):
        return self.request.user.is_staff


class QuestionTypeGeneratorView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "question_type_generator.html"

    def test_func(self):
        return self.request.user.is_staff
