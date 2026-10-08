from rest_framework import serializers

from apps.pricing.services import get_price_for
from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    variant_id = serializers.UUIDField(source="variant.public_id", read_only=True)
    product_name = serializers.CharField(source="variant.product.name", read_only=True)
    image_url = serializers.URLField(source="variant.product.image_url", read_only=True)
    size = serializers.CharField(source="variant.size", read_only=True)
    color = serializers.CharField(source="variant.color", read_only=True)
    unit_price = serializers.SerializerMethodField()
    available = serializers.IntegerField(source="variant.stock.available", read_only=True)

    def get_unit_price(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        return get_price_for(user, obj.variant, qty=obj.quantity)

    class Meta:
        model = CartItem
        fields = (
            "id",
            "variant_id",
            "product_name",
            "image_url",
            "size",
            "color",
            "unit_price",
            "available",
            "quantity",
        )


class CartItemAddSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=20, default=1)


class CartItemUpdateSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class CartItemDeleteSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(min_value=1)
