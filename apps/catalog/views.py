from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny

from .models import Category
from .serializers import CategorySerializer, ProductSerializer
from .services import get_saleable_products


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class BoundedSearchFilter(filters.SearchFilter):
    def get_search_terms(self, request):
        value = request.query_params.get(self.search_param, "")
        if len(value) > 100:
            raise ValidationError(
                {"search": "Search text must be 100 characters or fewer."}
            )
        return super().get_search_terms(request)


class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter]
    filterset_fields = {"category__slug": ["exact"], "featured": ["exact"]}
    search_fields = ["name", "description", "category__name"]

    def get_queryset(self):
        return get_saleable_products(user=self.request.user)
