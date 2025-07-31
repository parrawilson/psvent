from django import forms
from .models import Venta, DetalleVenta, Cliente, Timbrado
from almacen.models import Producto, Servicio, Almacen,Stock
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
            'class': 'form-control select2 producto-select',
            'data-placeholder': 'Seleccione un producto'
        }),
        required=False
    )
    
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2 servicio-select',
            'data-placeholder': 'Seleccione un servicio'
        }),
        required=False
    )
    
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2 almacen-select',
            'data-placeholder': 'Seleccione un almacén'
        }),
        required=False
    )
    
    almacen_servicio = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2 almacen-servicio-select',
            'data-placeholder': 'Almacén para servicio'
        }),
        required=False,
        label="Almacén Servicio"
    )
    
    class Meta:
        model = DetalleVenta
        fields = ['tipo', 'producto', 'servicio', 'cantidad', 'precio_unitario', 'tasa_iva', 'almacen', 'almacen_servicio']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-control tipo-select',
                'onchange': 'actualizarCampos(this)'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control cantidad-input',
                'min': 1,
                'data-stock-check': 'true'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control precio-input',
                'min': 0,
                'step': '0.01'
            }),
            'tasa_iva': forms.NumberInput(attrs={
                'class': 'form-control tasa-input',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar campos requeridos basados en el tipo
        if self.instance and self.instance.pk:
            if self.instance.tipo == 'PRODUCTO':
                self.fields['producto'].required = True
                self.fields['almacen'].required = True
            elif self.instance.tipo == 'SERVICIO':
                self.fields['servicio'].required = True
                if self.instance.servicio and self.instance.servicio.tipo == 'COMPUESTO':
                    self.fields['almacen_servicio'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        producto = cleaned_data.get('producto')
        servicio = cleaned_data.get('servicio')
        almacen = cleaned_data.get('almacen')
        almacen_servicio = cleaned_data.get('almacen_servicio')
        cantidad = cleaned_data.get('cantidad')
        
        # Validación básica de tipo
        if tipo == 'PRODUCTO':
            if not producto:
                self.add_error('producto', 'Debe seleccionar un producto')
            if not almacen:
                self.add_error('almacen', 'Debe seleccionar un almacén')
                
            # Validar stock
            if producto and almacen and cantidad:
                stock = Stock.objects.filter(
                    producto=producto,
                    almacen=almacen
                ).first()
                
                if stock and stock.cantidad < cantidad:
                    self.add_error('cantidad', f'Stock insuficiente. Disponible: {stock.cantidad}')
        
        elif tipo == 'SERVICIO':
            if not servicio:
                self.add_error('servicio', 'Debe seleccionar un servicio')
            
            # Validar componentes para servicios compuestos
            if servicio and servicio.tipo == 'COMPUESTO' and not almacen_servicio:
                self.add_error('almacen_servicio', 'Debe seleccionar un almacén para el servicio')
                
            # Validar stock de componentes para servicios compuestos
            if (servicio and servicio.tipo == 'COMPUESTO' and 
                almacen_servicio and cantidad):
                
                for componente in servicio.componentes.all():
                    cantidad_necesaria = componente.cantidad * cantidad
                    stock = Stock.objects.filter(
                        producto=componente.producto,
                        almacen=almacen_servicio
                    ).first()
                    
                    if not stock or stock.cantidad < cantidad_necesaria:
                        self.add_error(None, 
                            f'Stock insuficiente de {componente.producto.nombre} para el servicio {servicio.nombre}. '
                            f'Necesario: {cantidad_necesaria}, Disponible: {stock.cantidad if stock else 0}'
                        )
        
        # Validar que se haya seleccionado producto o servicio según el tipo
        if tipo == 'PRODUCTO' and not producto:
            self.add_error('producto', 'Debe seleccionar un producto para este tipo')
        elif tipo == 'SERVICIO' and not servicio:
            self.add_error('servicio', 'Debe seleccionar un servicio para este tipo')
        
        # Validar que no se mezclen producto y servicio
        if producto and servicio:
            self.add_error(None, 'No puede seleccionar tanto un producto como un servicio')
        
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

    # Campo para almacén de servicios (solo visible si hay servicios que consumen productos)
    almacen_servicios = forms.ModelChoiceField(
        required=False,
        queryset=Almacen.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Almacén para servicios',
        help_text='Seleccione el almacén del que se descontarán los productos usados en servicios'
    )

    # Nuevo campo booleano para generar documento
    generar_documento = forms.BooleanField(
        required=False,
        initial=True,
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
            
            # Establecer almacén principal como predeterminado para servicios
            almacen_principal = Almacen.objects.filter(es_principal=True).first()
            if almacen_principal:
                self.fields['almacen_servicios'].initial = almacen_principal
        
        # Mostrar campo de almacén de servicios solo si hay servicios que consumen productos
        if self.venta and self.venta.tiene_servicios_con_inventario():
            self.fields['almacen_servicios'].required = True
            self.fields['almacen_servicios'].widget.attrs['required'] = 'required'
        else:
            self.fields['almacen_servicios'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        tipo_documento = cleaned_data.get('tipo_documento')
        
        # Validar timbrado para documentos fiscales
        if tipo_documento in ['F', 'BV'] and not cleaned_data.get('timbrado'):
            self.add_error('timbrado', 'Este tipo de documento requiere timbrado')
        
        # Validar almacén para servicios si es necesario
        if (self.venta and self.venta.tiene_servicios_con_inventario() and 
            not cleaned_data.get('almacen_servicios')):
            self.add_error('almacen_servicios', 'Debe seleccionar un almacén para los servicios')
        
        return cleaned_data

    def save(self):
        """Procesa los datos del formulario y finaliza la venta"""
        if not self.venta:
            raise ValidationError("No hay una venta asociada a este formulario")
        
        # Obtener datos del formulario
        caja = self.cleaned_data['caja']
        tipo_pago = self.cleaned_data['tipo_pago']
        tipo_documento = self.cleaned_data['tipo_documento']
        condicion = self.cleaned_data['condicion']
        timbrado = self.cleaned_data.get('timbrado')
        almacen_servicios = self.cleaned_data.get('almacen_servicios')
        generar_documento = self.cleaned_data.get('generar_documento', False)
        
        # Asignar almacén de servicios a los detalles que lo necesiten
        if almacen_servicios:
            for detalle in self.venta.detalles.filter(tipo='SERVICIO', servicio__tipo='COMPUESTO'):
                if not detalle.almacen_servicio:
                    detalle.almacen_servicio = almacen_servicios
                    detalle.save()
        
        # Finalizar la venta
        self.venta.finalizar(
            caja=caja,
            tipo_pago=tipo_pago,
            tipo_documento=tipo_documento,
            condicion=condicion,
            timbrado=timbrado
        )
        
        return {
            'venta': self.venta,
            'generar_documento': generar_documento
        }




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