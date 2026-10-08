from django.urls import path

from .views import CsrfView, LoginView, LogoutView, RefreshView

urlpatterns = [
    path("csrf/", CsrfView.as_view()),
    path("token/", LoginView.as_view()),
    path("token/refresh/", RefreshView.as_view()),
    path("token/logout/", LogoutView.as_view()),
]
