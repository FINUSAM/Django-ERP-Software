# forms.py
from django import forms
from django.forms.models import inlineformset_factory
from .models import SalesBill
from transactions.models import Sale

class SalesBillForm(forms.ModelForm):
    class Meta:
        model = SalesBill
        fields = ['sales_bill_type', 'customer', 'fund', 'discount_price']
        widgets = {
            'discount_price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['stockset', 'quantity', 'price_per_unit', 'return_quantity', 'return_price_per_unit']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'step': '1'}),
            'price_per_unit': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'return_quantity': forms.NumberInput(attrs={'min': 0, 'step': '1'}),
            'return_price_per_unit': forms.NumberInput(attrs={'min': 0, 'step': '0.01'})
        }

SaleFormSet = inlineformset_factory(
    SalesBill, Sale,
    form=SaleForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)

