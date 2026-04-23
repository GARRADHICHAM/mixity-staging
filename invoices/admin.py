from django.contrib import admin

from invoices.models import Invoice


class InvoiceAdmin(admin.ModelAdmin):

    list_display = ["__str__", "subscription"]

    class Meta:
        fields = "__all__"


admin.site.register(Invoice, InvoiceAdmin)
