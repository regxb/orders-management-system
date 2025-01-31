import pytest
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_create_order(client, item):
    url = "/api/orders/"
    data = {
        "table_number": 1,
        "items": [{"item_id": 1, "price": 100}]
    }
    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "table_number" in response.data
    assert "items" in response.data


@pytest.mark.django_db
def test_update_order(client, order):
    url = f"/api/orders/{order.id}/"
    data = {
        "status": "ready",
        "items": [{"item_id": 2, "price": 120}]
    }
    response = client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "ready"


@pytest.mark.django_db
def test_delete_order(client, order, item):
    url = f"/api/orders/{order.id}/"
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Order.objects.filter(id=order.id).exists()


@pytest.mark.django_db
def test_get_orders(client, item):
    url = "/api/orders/list/"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_find_orders(client, order, item):
    url = "/api/orders/search/"
    response = client.get(url, {"status": "pending"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) > 0
