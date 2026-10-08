from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CartItemAddSerializer,
    CartItemDeleteSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
)
from .services import (
    CartOperationError,
    add_item,
    get_cart_items,
    remove_item,
    update_item,
)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = get_cart_items(request.user)
        serializer = CartItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        input_serializer = CartItemAddSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            item = add_item(
                user=request.user,
                variant_public_id=input_serializer.validated_data["variant_id"],
                quantity=input_serializer.validated_data["quantity"],
            )
        except CartOperationError as exc:
            return self._error_response(exc)

        return Response(
            CartItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        input_serializer = CartItemUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            item = update_item(
                user=request.user,
                item_id=input_serializer.validated_data["item_id"],
                quantity=input_serializer.validated_data["quantity"],
            )
        except CartOperationError as exc:
            return self._error_response(exc)

        return Response(CartItemSerializer(item).data)

    def delete(self, request):
        input_serializer = CartItemDeleteSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        remove_item(
            user=request.user,
            item_id=input_serializer.validated_data["item_id"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _error_response(exc):
        return Response(
            {"detail": str(exc)},
            status=exc.status_code,
        )
