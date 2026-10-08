from django.urls import path

from .views import CheckoutView, OrderList

urlpatterns = [
    path("", OrderList.as_view()),
    path("checkout/", CheckoutView.as_view()),
]
