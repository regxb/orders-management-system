from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import CreateOrderForm, UpdateOrderForm, OrderSearchForm, OrderItemFormSet
from .models import Order, Item
from .services.order_service import OrderCreateService, OrderUpdateService, OrderService


def get_orders(request: HttpRequest) -> HttpResponse:
    form = OrderSearchForm(request.GET)
    orders = Order.objects.all()
    try:
        orders = OrderService(form).get(orders).order_by("id")
    except Exception as e:
        messages.error(request, e.args[0])

    return render(request, "orders/order_list.html", {"form": form, "orders": orders})


def create_order(request: HttpRequest) -> HttpResponse:
    context = {"items": Item.objects.values("name", "id"), 'form': CreateOrderForm}
    if request.method == 'POST':
        form = CreateOrderForm(request.POST)
        items = request.POST.getlist('items')
        prices = request.POST.getlist("prices")
        items_data = [{"item_id": item_data[0], "price": item_data[1]} for item_data in zip(items, prices)]
        try:
            OrderCreateService().create_order(form, items_data)
            messages.success(request, "Заказ успешно создан.")
            return redirect('order_list')
        except Exception as e:
            messages.error(request, e)

    return render(request, "orders/order_create.html", context)


def update_order(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        form = UpdateOrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, queryset=order.items.all())
        try:
            OrderUpdateService(form, order, formset).update_order()
            messages.success(request, "Заказ успешно обновлен.")
            return redirect('order_list')
        except Exception as e:
            messages.error(request, e.args[0])
    else:
        form = UpdateOrderForm(instance=order)
        formset = OrderItemFormSet(queryset=order.items.all())
    return render(request, 'orders/order_update.html', {'form': form, 'formset': formset})


def delete_order(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('order_list')


def revenue_report(request: HttpRequest) -> HttpResponse:
    paid_orders = Order.objects.filter(status='paid')
    total_revenue = 0
    for order in paid_orders:
        total_revenue += sum(item.price for item in order.items.all())

    return render(request, 'orders/revenue.html', {'total_revenue': total_revenue})
