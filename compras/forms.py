from django import forms
from .models import OrdenCompra, DetalleOrdenCompra, Proveedor,RecepcionCompra
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
    tipo_pago = forms.ChoiceField(
        choices=RecepcionCompra.TIPO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Pago *'
    )
    
    tipo_documento = forms.ChoiceField(
        choices=OrdenCompra.TIPO_DOCUMENTO,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'actualizarCamposDocumento()'  # JavaScript para cambios dinámicos
        }),
        label='Tipo de Documento *'
    )

    numero_documento = forms.CharField(
    widget=forms.TextInput(attrs={
        'class': 'form-control'
    }),
    label='No. de Documento *'
    )

    plazo_dias = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0'
        }),
        label='Plazo días',
        required=False,
        initial=0
    )

    timbrado = forms.CharField(
    widget=forms.TextInput(attrs={
        'class': 'form-control'
    }),
    label='Timbrado de Documento *'
    )
 
    condicion = forms.ChoiceField(
        choices=OrdenCompra.TIPO_CONDICION,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Condición de Venta *'
    )
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
    
    def clean_plazo_dias(self):
        plazo_dias = self.cleaned_data.get('plazo_dias', 0)
        condicion = self.cleaned_data.get('condicion')
        
        if condicion == '2' and plazo_dias <= 0:  # Crédito
            raise forms.ValidationError("Debe especificar un plazo mayor a 0 días para crédito")
        return plazo_dias




from django import forms
from .models import PagoProveedor
from caja.models import Caja
from django.utils import timezone

class PagoProveedorForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        self.cuenta = kwargs.pop('cuenta', None)  # Añade esta línea
        super().__init__(*args, **kwargs)
        if user:
            self.fields['caja'].queryset = Caja.objects.filter(
                estado='ABIERTA',
                responsable=user.perfil
            )
        # Configuración explícita del campo fecha_pago
        self.fields['fecha_pago'] = forms.DateField(
            widget=forms.DateInput(attrs={'type': 'date'}),
            initial=timezone.now().date()
        )
    
    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get('monto')
        
        if monto and monto <= 0:
            self.add_error('monto', "El monto debe ser mayor a cero")
        
        # Validar contra el saldo pendiente
        if monto and self.cuenta and monto > self.cuenta.saldo_pendiente:
            self.add_error('monto', "El monto no puede ser mayor al saldo pendiente")
        
        return cleaned_data
    
    class Meta:
        model = PagoProveedor
        fields = ['monto', 'forma_pago', 'fecha_pago', 'comprobante', 'caja', 'notas']
        widgets = {
            'monto': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }




