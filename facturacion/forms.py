# facturacion/forms.py
from django import forms


class DocumentoSearchForm(forms.Form):
    q = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'N° venta, código SET o cliente...',
            'class': 'form-control'
        })
    )




