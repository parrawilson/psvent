from django import forms
from .models import OrdenCompra, DetalleOrdenCompra, Proveedor
from almacen.models import Producto,Almacen
from caja.models import Caja

class ProveedorForm(forms.ModelForm):

    class Meta:
        model= Proveedor
        fields= [
            'ruc',
            'dv',
            'razon_social',
            'direccion',
            'telefono',
            'email',
            'activo',
        ]
        widgets= {
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RUC'
            }),
            'dv': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dígito verificador'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre o razón social'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Dirección'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels={
            'ruc': 'RUC',
            'dv': 'Dígito verificador (DV)',
            'razon_social': 'Nombre o razón social',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Correo electrónico',
            'activo': 'Proveedor activo'
        }


class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['proveedor', 'fecha_entrega', 'notas']
        widgets = {
            'fecha_entrega': forms.DateInput(attrs={'type': 'date'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

class DetalleOrdenCompraForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        label="Producto"
    )
    
    class Meta:
        model = DetalleOrdenCompra
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1}),
            'precio_unitario': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }

class RecibirOrdenForm(forms.Form):
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        label="Almacén de destino"
    )
    caja = forms.ModelChoiceField(
        queryset=Caja.objects.none(),  # Se actualiza en __init__
        label="Caja para pago",
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['caja'].queryset = Caja.objects.filter(
                estado='ABIERTA',
                responsable=user.perfil
            )
    
    def clean(self):
        cleaned_data = super().clean()
        caja = cleaned_data.get('caja')
        
        if caja and caja.estado != 'ABIERTA':
            raise forms.ValidationError('La caja seleccionada no está abierta')
        
        return cleaned_data