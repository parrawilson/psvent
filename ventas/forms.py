from django import forms
from .models import Venta, DetalleVenta, Cliente, Timbrado
from almacen.models import Producto, Almacen,Stock
from caja.models import Caja
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator


class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'pais_cod': forms.TextInput(attrs={'class': 'form-control'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'naturaleza': forms.Select(attrs={'class': 'form-control'}),
            't_contribuyente': forms.Select(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_cliente': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        naturaleza = cleaned_data.get('naturaleza')
        t_contribuyente = cleaned_data.get('t_contribuyente')

        if naturaleza == '1' and not t_contribuyente:
            self.add_error('t_contribuyente', 'Este campo es obligatorio para contribuyentes.')
        

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
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Caja *'
    )
    
    tipo_pago = forms.ChoiceField(
        choices=Venta.TIPO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Pago *'
    )
    
    tipo_documento = forms.ChoiceField(
        choices=Venta.TIPO_DOCUMENTO,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'actualizarCamposDocumento()'  # JavaScript para cambios dinámicos
        }),
        label='Tipo de Documento *'
    )
    condicion = forms.ChoiceField(
        choices=Venta.TIPO_CONDICION,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Condición de Venta *'
    )
    
    timbrado = forms.ModelChoiceField(
        required=False,
        queryset=Timbrado.objects.filter(estado='ACTIVO'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Timbrado'
    )

    # Nuevo campo booleano para generar documento
    generar_documento = forms.BooleanField(
        required=False,  # No es obligatorio
        initial=True,    # Por defecto marcado
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'generarDocumentoCheckbox'
        }),
        label='Generar documento XML y Kude',
        help_text='Desmarque esta opción si no desea generar los documentos ahora'
    )

    def __init__(self, *args, **kwargs):
        self.venta = kwargs.pop('venta', None)
        super().__init__(*args, **kwargs)
        
        # Si ya existe una venta, establecer valores iniciales
        if self.venta:
            self.fields['tipo_documento'].initial = self.venta.tipo_documento
            self.fields['condicion'].initial = self.venta.condicion
            self.fields['timbrado'].initial = self.venta.timbrado

    def clean(self):
        cleaned_data = super().clean()
        tipo_documento = cleaned_data.get('tipo_documento')
        
        # Validar timbrado para documentos fiscales
        if tipo_documento in ['F', 'BV'] and not cleaned_data.get('timbrado'):
            self.add_error('timbrado', 'Este tipo de documento requiere timbrado')
        
        return cleaned_data




class TimbradoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear las fechas para el input type="date" (requiere formato YYYY-MM-DD)
        if self.instance and self.instance.pk:
            self.initial['fecha_inicio'] = self.instance.fecha_inicio.strftime('%Y-%m-%d')
            self.initial['fecha_fin'] = self.instance.fecha_fin.strftime('%Y-%m-%d')

    class Meta:
        model = Timbrado
        fields = ['numero', 'tipo_emision', 'fecha_inicio', 'fecha_fin', 'activo']
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678',
                'pattern': '\d{8}',
                'title': 'Debe contener exactamente 8 dígitos'
            }),
            'tipo_emision': forms.Select(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'fecha_fin': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'style': 'margin-left: 0;'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio >= fecha_fin:
                self.add_error('fecha_fin', "La fecha de fin debe ser posterior a la fecha de inicio")
        
        return cleaned_data