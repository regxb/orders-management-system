from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction, DatabaseError, IntegrityError
from django.db.models import QuerySet

from orders.forms import OrderSearchForm, UpdateOrderForm, OrderItemFormSet, CreateOrderForm
from orders.models import OrderItem, Item, Order


class ItemNotFoundError(Exception):
    def __init__(self) -> None:
        self.message = "Блюдо не найдено."
        super().__init__(self.message)


class OrderService:
    def __init__(self, form: OrderSearchForm) -> None:
        self.form = form

    def get(self, orders: QuerySet[Order]) -> QuerySet[Order]:
        if self.form.is_valid():
            table_number = self.form.cleaned_data.get("table_number")
            status = self.form.cleaned_data.get("status")

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

    def create_order(self, form: CreateOrderForm, items_data: list[dict[str, Any]]) -> None:
        if form.is_valid():
            with transaction.atomic():
                order = form.save()
                self.create_order_items(items_data, order)
        else:
            raise ValueError("Некорректный номер стола.")

    @staticmethod
    def create_order_items(items_data: list[dict[str, Any]], order: Order) -> None:
        if items_data:
            all_items = []
            for item_data in items_data:
                try:
                    item_obj = Item.objects.get(id=item_data["item_id"])
                except Exception:
                    raise ItemNotFoundError()

                new_item = OrderItem(order=order, item=item_obj, price=item_data["price"])
                all_items.append(new_item)
            try:
                OrderItem.objects.bulk_create(all_items)
            except (IntegrityError, DatabaseError) as e:
                raise e
        else:
            raise ValidationError("Должно быть указано хотя бы одно блюдо.")


class OrderUpdateService:
    def __init__(self, form: UpdateOrderForm, order: Order, formset: OrderItemFormSet) -> None:
        self.form = form
        self.order = order
        self.formset = formset

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
        instances = formset.save(commit=False)

        for instance in instances:
            instance.order = self.order
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()
