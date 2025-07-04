from django import forms
from .models import Venta, DetalleVenta, Cliente
from almacen.models import Producto, Almacen
from caja.models import Caja

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
        }

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DetalleVentaForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario', 'almacen']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.01'
            }),
        }

class FinalizarVentaForm(forms.Form):
    caja = forms.ModelChoiceField(
        queryset=Caja.objects.filter(estado='ABIERTA'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_pago = forms.ChoiceField(
        choices=Venta.TIPO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )