from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("staff-console/", admin.site.urls),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/cart/", include("apps.cart.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
]
