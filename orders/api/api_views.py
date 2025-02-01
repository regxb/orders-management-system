from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.api.serializers import OrderCreateSerializer, OrderSerializer, OrderUpdateSerializer
from orders.models import Order, OrderItem
from orders.services.order_service import OrderCreateService


class OrderListCreateAPIView(APIView):
    @extend_schema(
        summary="Просмотр заказов",
        responses={
            201: OpenApiResponse(response=OrderSerializer),
        }
    )
    def get(self, request: Request) -> Response:
        orders = Order.objects.all()

        serializer = OrderSerializer(orders, many=True)
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
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            table_number = serializer.validated_data["table_number"]
            items_data = serializer.validated_data["items"]
            order: Order = Order.objects.create(table_number=table_number)
            try:
                OrderCreateService().create_order_items(items_data, order)
            except Exception as e:
                transaction.set_rollback(True)
                return Response({"error": str(e.args[0])}, status=status.HTTP_400_BAD_REQUEST)

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    @extend_schema(
        summary="Изменение данных заказа",
        request=OrderUpdateSerializer,
        responses={
            201: OpenApiResponse(response=OrderSerializer, description="Заказ успешно обновлен"),
            400: OpenApiResponse(description="Ошибки валидации"),
            404: OpenApiResponse(description="Заказ не найден"),
        }
    )
    def patch(self, request: Request, order_id: int) -> Response:
        serializer = OrderUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order = Order.objects.filter(id=order_id).first()
            if not order:
                return Response(
                    {"error": {"code": "order_not_found", "message": "Заказ не найден"}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            status_value = serializer.validated_data.get("status")
            if status_value:
                order.status = status_value
                order.save()

            items_data = serializer.validated_data.get("items", [])
            if items_data:
                order.items.all().delete()
                try:
                    OrderCreateService().create_order_items(items_data, order)
                except Exception as e:
                    transaction.set_rollback(True)
                    return Response({"error": str(e.args[0])}, status=status.HTTP_400_BAD_REQUEST)

            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Удаление заказа",
        responses={
            204: OpenApiResponse(description="Заказ успешно удален"),
            404: OpenApiResponse(description="Заказ не найден"),
        }
    )
    def delete(self, request: Request, order_id: int) -> Response:
        order = Order.objects.filter(id=order_id).first()
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
        status_param = request.GET.get("status")
        table_id = request.GET.get("table_id")

        if table_id:
            orders = orders.filter(table_number=table_id)

        if status_param:
            orders = orders.filter(status=status_param)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
