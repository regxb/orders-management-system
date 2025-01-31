import pytest
from django.forms import model_to_dict
from django.urls import reverse
from rest_framework import status

from orders.forms import UpdateOrderForm, OrderItemFormSet
from orders.models import Order
from orders.services.order_service import OrderUpdateService


@pytest.mark.django_db
def test_get_orders(client):
    Order.objects.create(table_number=1, status='pending')
    Order.objects.create(table_number=2, status='ready')

    url = reverse('order_list')
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.context['orders']) == 2
    assert 'form' in response.context


@pytest.mark.django_db
def test_create_order(client, item):
    url = reverse('order_create')
    data = {
        'table_number': 1,
        'items': [item.id],
        'prices': [100]
    }

    response = client.post(url, data)

    assert response.status_code == status.HTTP_200_OK
    assert Order.objects.count() == 1
    assert Order.objects.first().table_number == 1


@pytest.mark.django_db
def test_update_order(order, order_item):
    updated_data = model_to_dict(order)
    updated_data["status"] = "ready"

    form = UpdateOrderForm(data=updated_data, instance=order)

    formset_data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-0-id": order_item.id,
        "form-0-item": order_item.item.id,
        "form-0-price": "600"
    }
    formset = OrderItemFormSet(data=formset_data, queryset=order.items.all())

    service = OrderUpdateService(form, order, formset)
    service.update_order()

    order.refresh_from_db()
    order_item.refresh_from_db()

    assert order.status == "ready"
    assert order_item.price == 600


@pytest.mark.django_db
def test_delete_order(client, order):
    url = reverse('order_delete', args=[order.id])
    response = client.post(url)

    assert response.status_code == status.HTTP_302_FOUND
    assert not Order.objects.filter(id=order.id).exists()


@pytest.mark.django_db
def test_revenue_report(client, paid_order):
    url = reverse('revenue')
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert 'total_revenue' in response.context
    assert response.context['total_revenue'] == 1
