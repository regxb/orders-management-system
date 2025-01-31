from rest_framework import serializers

from orders.models import Order, OrderItem


class OrderItemCreateSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderCreateSerializer(serializers.Serializer):
    table_number = serializers.IntegerField()
    items = OrderItemCreateSerializer(many=True)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "table_number", "status", "items"]


class OrderItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['item', 'price']


class OrderUpdateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)


class OrderDeleteSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
