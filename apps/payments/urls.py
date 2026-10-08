from django.urls import path

from .views import (
    PaymentInitializeView,
    PaymentStatusView,
    PaymentVerifyView,
    PaymentWebhookView,
)

urlpatterns = [
    path("status/", PaymentStatusView.as_view()),
    path("initialize/", PaymentInitializeView.as_view()),
    path("verify/", PaymentVerifyView.as_view()),
    path("webhooks/<str:provider>/", PaymentWebhookView.as_view()),
]
