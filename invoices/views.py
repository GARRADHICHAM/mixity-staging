import datetime
import io
import os
import textwrap


# import payplug
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.
from constance import config as constanceconfig
from django.http.response import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import FormView, TemplateView, DetailView
from django.views.generic.base import View
from django import forms

from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from invoices.models import Invoice
from subscriptions.models import SubscriptionOption, SubscriptionPack, Product
from django.utils.translation import ugettext_lazy as _
from reportlab.pdfgen import canvas


class InvoiceView(UserPassesTestMixin, LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = "invoices/invoice.html"

    def __init__(self):
        super(InvoiceView, self).__init__()
        self._sub_opt = None

    def get_subscription_option(self):
        if not self._sub_opt:
            self._sub_opt = SubscriptionOption.objects.get(
                subscriptionPack__invoice=self.get_object()
            )
        return self._sub_opt

    def test_func(self):
        return (
            self.request.user.is_staff
            or self.request.user
            in self.get_subscription_option().subscriptionPack.structure.owners
        )

    def get(self, *args, **kwargs):
        pdfmetrics.registerFont(
            TTFont(
                "Arial", os.path.join(settings.STATICFILES_DIRS[0], "fonts/arial.ttf")
            )
        )
        pdfmetrics.registerFont(
            TTFont(
                "Arial-Bold",
                os.path.join(settings.STATICFILES_DIRS[0], "fonts/arialbd.ttf"),
            )
        )

        subscription_option = self.get_subscription_option()
        year = str(subscription_option.start_date.year)
        subscription_name = subscription_option.product.label
        invoice_number = f"S{subscription_option.start_date.strftime('%Y%m%d')}-{self.get_object().id}"
        date = subscription_option.start_date.strftime("%d/%m/%Y")
        designation = f"{subscription_option.product.label} : {subscription_option.product.description}"
        structure_name = (
            subscription_option.subscriptionPack.structure.commercial_name
            or subscription_option.subscriptionPack.structure.juridic_name
        )
        structure_address = str(
            subscription_option.subscriptionPack.structure.address
        ).split(", ")
        num_tva = subscription_option.subscriptionPack.structure.num_tva_intracom or ""

        quantity = 1
        discount = self.get_object().discount
        price_ht = self.get_object().tax_free_price
        price_ttc = self.get_object().tax_included_price
        tva = self.get_object().tax
        if price_ht and tva:
            vat_rate = round((tva * 100) / price_ht, 2)
        else:
            vat_rate = 0

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(800, 1000), bottomup=0)

        # Logo Section
        # Setting th origin to (10,40)
        c.translate(40, 160)
        # Inverting the scale for getting mirror Image of logo
        c.scale(4, -4)
        # Inserting Logo into the Canvas at required position
        c.drawImage(
            os.path.join(settings.STATICFILES_DIRS[0], "img/logo-mixity-white-bg.png"),
            0,
            8,
            width=50,
            height=16.37,
        )

        # Title Section
        # Again Inverting Scale For strings insertion
        c.scale(1, -1)
        # Again Setting the origin back to (0,0) of top-left
        c.translate(-10, -40)
        # Setting the font for Name title of company
        c.setFont("Arial-Bold", 10)
        # Inserting the name of the company
        c.drawCentredString(125, 19, "SAS Mixity")
        # For under lining the title
        c.line(70, 23, 180, 23)
        # Changing the font size for Specifying Address
        c.setFont("Arial-Bold", 5)
        c.drawCentredString(125, 30, "6 Rue Edouard Nignon, 44300 Nantes, France")
        c.drawCentredString(
            125, 35, "Tel: +33 6 07 35 78 29   |   Mail: contact@mixity.co"
        )
        # Changing the font size for Specifying GST Number of firm
        c.setFont("Arial-Bold", 6)

        # Line Seprating the page header from the body
        c.line(5, 38, 195, 38)

        # Document Information
        # Changing the font for Document title
        c.setFont("Arial-Bold", 8)
        c.drawCentredString(100, 48, str(_("FACTURE")))

        # This Block Consist of Costumer Details
        c.roundRect(15, 53, 170, 56, 10, stroke=1, fill=0)
        c.setFont("Arial-Bold", 5)
        c.drawRightString(70, 60, _("Numéro de facture") + " :")
        c.drawRightString(70, 70, _("Date") + " :")
        c.drawRightString(70, 80, _("Client") + " :")
        c.drawRightString(70, 90, _("Adresse") + " :")
        c.drawRightString(70, 105, _("Numéro de TVA") + " :")
        c.setFont("Arial", 5)

        c.drawString(71, 60, invoice_number)
        c.drawString(71, 70, date)
        c.drawString(71, 80, structure_name)
        c.drawString(71, 90, structure_address[0])

        addresss_line2 = ""
        for i in range(1, len(structure_address)):
            addresss_line2 += structure_address[i] + ", "
        c.drawString(71, 96, addresss_line2[:-2])
        c.drawString(71, 105, num_tva or "  /")
        c.setFont("Arial-Bold", 5)

        # This Block Consist of Item Description
        c.roundRect(15, 118, 170, 70, 10, stroke=1, fill=0)
        c.line(15, 130, 185, 130)
        c.drawCentredString(65, 127, str(_("Désignation")))
        c.drawCentredString(124, 127, str(_("Quantité")))
        c.drawCentredString(160, 127, str(_("Montant HT")))
        # Drawing table for Item Description
        c.line(110, 118, 110, 188)
        c.line(137, 118, 137, 188)

        c.setFont("Arial", 4)
        # wrap text to fit in the name column
        designation = textwrap.wrap(designation, width=45)
        for i, value in enumerate(designation):
            c.drawString(18, 136 + i * 5, value)
        middle_line_position = 136 + (len(designation) - 1) * 5 / 2
        c.drawCentredString(124, middle_line_position, "1")
        c.drawCentredString(160, middle_line_position, str(price_ht))
        c.drawRightString(185, 115, str(_("Mode de paiement : Paiement en ligne")))

        # Total price infos
        c.setFont("Arial-Bold", 6)
        if discount > 0:
            discount_gap = 8
            c.drawString(100, 204, str(_("REDUCTION")))
        else:
            discount_gap = 0
        c.drawString(100, 196, str(_("TOTAL HT")))
        c.drawString(100, 204 + discount_gap, _("TVA") + " " + str(int(vat_rate)) + "%")
        c.line(100, 207 + discount_gap, 185, 207 + discount_gap)
        c.drawString(100, 214 + discount_gap, str(_("TOTAL TTC")))

        c.setFont("Arial", 6)
        c.drawRightString(185, 196, str(price_ht + discount) + " €")
        if discount > 0:
            c.drawRightString(185, 204, str(discount) + " €")
        c.drawRightString(185, 204 + discount_gap, str(tva) + " €")
        c.drawRightString(185, 214 + discount_gap, str(price_ttc) + " €")

        c.setFont("Arial", 3)
        # Footer infos
        c.drawCentredString(100, 230, str(_("SAS au capital de 25 000 euros")))
        c.drawCentredString(
            100, 234, str(_("Siret : 848 373 023 00011 - RCS : NANTES - NAF : 6201Z"))
        )
        c.drawCentredString(
            100, 238, str(_("TVA Intracommunautaire : FR 04 848 373 023"))
        )
        c.drawCentredString(100, 242, str(_("Page 1/1")))

        # End the Page and Start with new
        c.showPage()
        # Saving the PDF
        c.save()

        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f'filename="{_("Facture")}_{invoice_number}_{slugify(structure_name)}.pdf"'
        return response
