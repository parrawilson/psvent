from django import forms
from .models import Caja, MovimientoCaja
from usuarios.models import PerfilUsuario

class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['nombre', 'saldo_inicial', 'responsable']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'responsable': forms.Select(attrs={'class': 'form-control'}),
        }

class AperturaCajaForm(forms.Form):
    saldo_inicial = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'})
    )

class MovimientoCajaForm(forms.ModelForm):
    class Meta:
        model = MovimientoCaja
        fields = ['tipo', 'monto', 'descripcion', 'comprobante']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'comprobante': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CierreCajaForm(forms.Form):
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )