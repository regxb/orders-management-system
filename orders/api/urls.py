from django.urls import path

from .api_views import OrderListCreateAPIView, OrderDetailView, OrderSearchAPIView

urlpatterns = [
    path('orders/', OrderListCreateAPIView.as_view(), name='order-api-create'),
    path('orders/', OrderListCreateAPIView.as_view(), name='order-api-list'),
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-api-detail'),
    path('orders/search/', OrderSearchAPIView.as_view(), name='order-api-search'),
]
