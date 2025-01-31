from typing import List, Optional, Type

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet

from orders.models import OrderItem, Item, Order
from orders.forms import OrderSearchForm, UpdateOrderForm, OrderItemFormSet


class ItemNotFoundError(Exception):
    def __init__(self) -> None:
        self.message: str = "Блюдо не найдено."
        super().__init__(self.message)


class OrderService:
    def __init__(self, form: OrderSearchForm) -> None:
        self.form: OrderSearchForm = form

    def get(self, orders: QuerySet[Order]) -> QuerySet[Order]:
        if self.form.is_valid():
            table_number: Optional[int] = self.form.cleaned_data.get("table_number")
            status: Optional[str] = self.form.cleaned_data.get("status")

            if table_number:
                orders = orders.filter(table_number=table_number)

            if status:
                if status not in dict(Order.STATUS_CHOICES).keys():
                    raise ValidationError("Недопустимый статус заказа!")
                orders = orders.filter(status=status)
        else:
            raise ValidationError("Некорректные данные для поиска")
        return orders


class OrderCreateService:
    def __init__(self, form: Type[Order], items: List[str], prices: List[str]) -> None:
        self.form: Type[Order] = form
        self.items: List[str] = items
        self.prices: List[str] = prices

    def create_order(self) -> None:
        if self.form.is_valid():
            with transaction.atomic():
                order: Order = self.form.save()
                self._create_order_items(order)
        else:
            raise ValueError("Некорректный номер стола.")

    def _create_order_items(self, order: Order) -> None:
        if any(self.items) and any(self.prices):
            all_items: List[OrderItem] = []
            for item, price in zip(self.items, self.prices):
                try:
                    item_id: int = int(item)
                    item_obj: Item = Item.objects.get(id=item_id)
                except Exception:
                    raise ItemNotFoundError()

                new_item = OrderItem(order=order, item=item_obj, price=price)
                all_items.append(new_item)
            OrderItem.objects.bulk_create(all_items)
        else:
            raise ValidationError("Выберите хотя бы одно блюдо.")


class OrderUpdateService:
    def __init__(self, form: UpdateOrderForm, order: Order, formset: OrderItemFormSet) -> None:
        self.form: UpdateOrderForm = form
        self.order: Order = order
        self.formset: OrderItemFormSet = formset

    def update_order(self) -> None:
        if not self.form.is_valid():
            raise ValidationError("Некорректный статус заказа.")

        if not self.formset.is_valid():
            raise ValidationError("Ошибка при заполнении блюд в заказе.")

        try:
            with transaction.atomic():
                self.form.save()
                self._update_order_items(self.formset)

                if not self.order.items.exists():
                    self.order.delete()

        except Item.DoesNotExist:
            raise ItemNotFoundError()
        except ValidationError as e:
            raise e
        except Exception as e:
            raise Exception(f"Ошибка при обновлении заказа: {str(e)}")

    def _update_order_items(self, formset: OrderItemFormSet) -> None:
        instances: List[OrderItem] = formset.save(commit=False)

        for instance in instances:
            instance.order = self.order
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()
