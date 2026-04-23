from django.contrib import admin


# Register your models here.
from payments.models import CheckoutSession


class CheckoutSessionAdmin(admin.ModelAdmin):
    list_display = ["subscription", "expires_at", "payment_status"]
    readonly_fields = ["payment_intent", "checkout_id", "expires_at", "payment_status"]


admin.site.register(CheckoutSession, CheckoutSessionAdmin)
