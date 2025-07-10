from django import forms
from .models import Venta, DetalleVenta, Cliente
from almacen.models import Producto, Almacen,Stock
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
            'tipo_cliente': forms.Select(attrs={'class': 'form-control'}),
        }

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'tipo_documento', 'numero_documento', 'timbrado', 'condicion', 'notas']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'timbrado': forms.TextInput(attrs={'class': 'form-control'}),
            'condicion': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DetalleVentaForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Seleccione un producto'
        })
    )
    
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Seleccione un almacén'
        })
    )
    
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario', 'tasa_iva', 'almacen']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'data-stock-check': 'true'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.01'
            }),
            'tasa_iva': forms.NumberInput(attrs={
                'class': 'form-control',
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        almacen = cleaned_data.get('almacen')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and almacen and cantidad:
            stock = Stock.objects.filter(
                producto=producto,
                almacen=almacen
            ).first()
            
            if stock and stock.cantidad < cantidad:
                raise forms.ValidationError(
                    f'Stock insuficiente. Disponible: {stock.cantidad}'
                )
        
        return cleaned_data


class FinalizarVentaForm(forms.Form):
    caja = forms.ModelChoiceField(
        queryset=Caja.objects.filter(estado='ABIERTA'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_pago = forms.ChoiceField(
        choices=Venta.TIPO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )