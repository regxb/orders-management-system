from typing import List, Dict, Union, Optional

from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.api.serializers import OrderCreateSerializer, OrderSerializer, OrderUpdateSerializer
from orders.models import Item, Order, OrderItem


class OrderListCreateAPIView(APIView):
    @extend_schema(
        summary="Просмотр заказов",
        responses={
            201: OpenApiResponse(response=OrderSerializer),
            400: OpenApiResponse(description="Ошибки валидации"),
        }
    )
    def get(self, request: Request) -> Response:
        orders = Order.objects.all()

        serializer: OrderSerializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Создание нового заказа",
        request=OrderCreateSerializer,
        responses={
            201: OpenApiResponse(response=OrderCreateSerializer, description="Заказ успешно создан"),
            400: OpenApiResponse(description="Ошибки валидации"),
        }
    )
    def post(self, request: Request) -> Response:
        serializer: OrderCreateSerializer = OrderCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            table_number: int = serializer.validated_data["table_number"]
            items_data: List[Dict[str, Union[int, float]]] = serializer.validated_data["items"]

            order: Order = Order.objects.create(table_number=table_number)
            order_items: Union[List[OrderItem], Response] = self.create_order_items(order, items_data)

            if isinstance(order_items, Response):
                return order_items

            OrderItem.objects.bulk_create(order_items)
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def create_order_items(order: Order, items_data: List[Dict[str, Union[int, float]]]) -> Union[
        List[OrderItem], Response]:
        order_items: List[OrderItem] = []
        for item_data in items_data:
            try:
                item: Item = Item.objects.get(id=item_data["item_id"])
                price: float = float(item_data["price"])
                if price <= 0 or price >= 100_000_000:
                    return Response(
                        {"error": {"code": "invalid_price", "message": "Некорректная цена."}},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                order_items.append(OrderItem(order=order, item=item, price=price))
            except Item.DoesNotExist:
                return Response(
                    {"error": {"code": "item_not_found", "message": f"Блюдо с ID {item_data['item_id']} не найдено"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return order_items


class OrderDetailView(APIView):
    @extend_schema(
        summary="Изменение данных заказа",
        request=OrderUpdateSerializer,
        responses={
            201: OpenApiResponse(response=OrderSerializer, description="Заказ успешно обновлен"),
            400: OpenApiResponse(description="Ошибки валидации"),
        }
    )
    def patch(self, request: Request, order_id: int) -> Response:
        serializer: OrderUpdateSerializer = OrderUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order: Optional[Order] = Order.objects.filter(id=order_id).first()
            if not order:
                return Response(
                    {"error": {"code": "order_not_found", "message": "Заказ не найден"}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            status_value: Optional[str] = serializer.validated_data.get("status")
            if status_value:
                order.status = status_value
                order.save()

            items_data: List[Dict[str, Union[int, float]]] = serializer.validated_data.get("items", [])
            if items_data:
                order.items.all().delete()
                order_items: Union[List[OrderItem], Response] = OrderListCreateAPIView.create_order_items(order, items_data)
                if isinstance(order_items, Response):
                    return order_items
                OrderItem.objects.bulk_create(order_items)

            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление заказа",
        responses={
            201: OpenApiResponse(description="Заказ успешно удален"),
            400: OpenApiResponse(description="Ошибки валидации"),
        }
    )
    def delete(self, request: Request, order_id: int) -> Response:
        order: Optional[Order] = Order.objects.filter(id=order_id).first()
        if not order:
            return Response(
                {"error": {"code": "order_not_found", "message": "Заказ не найден"}},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            OrderItem.objects.filter(order=order).delete()
            order.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderSearchAPIView(APIView):
    @extend_schema(
        summary="Поиск заказов",
        responses={200: OrderSerializer},
        parameters=[
            OpenApiParameter("status", str, description="Статус заказа", required=False),
            OpenApiParameter("table_id", int, description="Номер стола", required=False),
        ]
    )
    def get(self, request: Request) -> Response:
        orders = Order.objects.all()
        status_param: Optional[str] = request.GET.get("status")
        table_id: Optional[str] = request.GET.get("table_id")

        if table_id:
            orders = orders.filter(table_number=table_id)

        if status_param:
            orders = orders.filter(status=status_param)

        serializer: OrderSerializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
