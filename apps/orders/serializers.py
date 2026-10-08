from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product_name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("name", "sku", "quantity", "unit_price")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ("public_id", "status", "total", "currency", "created_at", "items")
        read_only_fields = fields
