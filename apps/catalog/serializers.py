from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from apps.pricing.services import get_price_for
from .models import Category, Product, Variant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "slug")


class VariantSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()

    def get_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return get_price_for(user, obj, qty=1)

    def get_in_stock(self, obj):
        try:
            return obj.stock.available
        except ObjectDoesNotExist:
            return 0

    class Meta:
        model = Variant
        fields = ("public_id", "sku", "size", "color", "price", "in_stock")


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "public_id",
            "name",
            "slug",
            "description",
            "image_url",
            "category",
            "variants",
            "featured",
        )
