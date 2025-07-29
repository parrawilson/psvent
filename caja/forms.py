from django import forms
from .models import Caja, MovimientoCaja
from usuarios.models import PerfilUsuario
from ventas.models import Venta
from compras.models import OrdenCompra

class CajaForm(forms.ModelForm):
    class Meta:
        model = Caja
        fields = ['nombre', 'punto_expedicion', 'responsable']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_expedicion': forms.Select(attrs={'class': 'form-control'}),
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
        fields = ['tipo', 'monto', 'descripcion', 'comprobante', 'imagen_comprobante', 'venta', 'compra']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del movimiento'
            }),
            'comprobante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de comprobante'
            }),
            'imagen_comprobante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'venta': forms.Select(attrs={'class': 'form-control'}),
            'compra': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'imagen_comprobante': 'Imagen de Comprobante (Opcional)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['venta'].queryset = Venta.objects.all()
        self.fields['compra'].queryset = OrdenCompra.objects.all()

class CierreCajaForm(forms.Form):
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full py-2 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500',
            'rows': 3,
            'placeholder': 'Observaciones sobre el cierre (diferencia, problemas, etc.)'
        })
    )
    
    confirmar_saldo = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded',
            'id': 'confirmar-saldo'
        }),
        label="Confirmo que el saldo físico coincide con el saldo calculado"
    )