from django.urls import path

from .views import CategoryList, ProductList

urlpatterns = [
    path("categories/", CategoryList.as_view()),
    path("products/", ProductList.as_view()),
]
