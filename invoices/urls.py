from django.contrib.auth.views import LogoutView
from django.urls import path

from invoices.views import InvoiceView

"""from invoices.views import PurchaseView, PurchaseSuccessView, PurchaseCancelView, PurchaseIPNView

urlpatterns = [
    path('purchase/', PurchaseView.as_view(), name='purchase'),
    path('success/', PurchaseSuccessView.as_view(), name='payment-success'),
    path('cancel/', PurchaseCancelView.as_view(), name='payment-cancel'),
    path('ipn/', PurchaseIPNView.as_view(), name='payment-ipn'),
]
"""
app_name = "invoices"
urlpatterns = [
    path("<int:pk>/view/", InvoiceView.as_view(), name="view"),
]
