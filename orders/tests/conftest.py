import pytest

from orders.models import Item, Order, OrderItem


@pytest.fixture
def item():
    item = Item.objects.create(name='test')
    return item


@pytest.fixture
def order(item):
    order = Order.objects.create(table_number=1)
    OrderItem.objects.create(order=order, item=item, price=1)
    return order


@pytest.fixture
def paid_order(item):
    order = Order.objects.create(table_number=1, status="paid")
    OrderItem.objects.create(order=order, item=item, price=1)
    return order


@pytest.fixture
def order_item(order, item):
    return OrderItem.objects.create(order=order, item=item, price=500)
