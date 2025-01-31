from django import forms
from django.forms import modelformset_factory

from .models import Order, OrderItem



class CreateOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['table_number']
        labels = {
            'table_number': 'Номер стола'
        }

    def clean_table_number(self):
        table_number = self.cleaned_data.get('table_number')

        if table_number <= 0:
            raise forms.ValidationError("Номер стола должен быть больше нуля.")

        return table_number


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['item', 'price']
        labels = {
            'item': 'Блюдо',
            'price': 'Цена',
        }

OrderItemFormSet = modelformset_factory(OrderItem, form=OrderItemForm, extra=0, can_delete=True)


class UpdateOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        labels = {
            'status': 'Статус'
        }
        widgets = {
            'status': forms.Select(choices=Order.STATUS_CHOICES)
        }


class OrderSearchForm(forms.Form):
    table_number = forms.IntegerField(required=False)
    status = forms.ChoiceField(choices=[('', 'Все статусы')] + Order.STATUS_CHOICES, required=False, )
