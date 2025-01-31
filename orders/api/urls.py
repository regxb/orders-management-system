from django.urls import path

from .api_views import CreateOrderApiView, OrderUpdateAPIView, OrderListAPIView, OrderFindAPIView

urlpatterns = [
    path('orders/', CreateOrderApiView.as_view(), name='order-api-create'),
    path('orders/list/', OrderListAPIView.as_view(), name='order-api-list'),
    path('orders/<int:order_id>/', OrderUpdateAPIView.as_view(), name='order-api-detail'),
    path('orders/search/', OrderFindAPIView.as_view(), name='order-api-search'),
]
