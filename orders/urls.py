from django.urls import path

from .views import get_orders, create_order, delete_order, update_order, revenue_report

urlpatterns = [
    path('', get_orders, name='order_list'),
    path('create/', create_order, name='order_create'),
    path('delete/<int:order_id>/', delete_order, name='order_delete'),
    path('update/<int:order_id>/', update_order, name='order_update'),
    path('revenue/', revenue_report, name='revenue'),
]
