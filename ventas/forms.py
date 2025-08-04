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
            'onchange': 'actualizarCamposDocumento()'
        }),
        label='Tipo de Documento *'
    )
    
    condicion = forms.ChoiceField(
        choices=Venta.TIPO_CONDICION,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'actualizarCamposCredito(this)'
        }),
        label='Condición de Venta *'
    )
    
    # Campos para crédito (condicionales)
    entrega_inicial = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'disabled': 'disabled'
        }),
        label='Entrega Inicial (Gs.)'
    )
    
    dia_vencimiento = forms.IntegerField(
        required=False,
        initial=5,
        min_value=1,
        max_value=28,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'disabled': 'disabled'
        }),
        label='Día de Vencimiento (1-28)'
    )
    
    fecha_primer_vencimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'disabled': 'disabled'
        }),
        label='Fecha Primer Vencimiento'
    )
    
    numero_cuotas = forms.IntegerField(
        required=False,
        initial=1,
        min_value=1,
        max_value=36,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'disabled': 'disabled',
            'id': 'id_numero_cuotas'
        }),
        label='Número de Cuotas'
    )
    
    monto_cuota = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'disabled': 'disabled',
            'id': 'id_monto_cuota'
        }),
        label='Monto por Cuota (Gs.)'
    )
    
    timbrado = forms.ModelChoiceField(
        required=False,
        queryset=Timbrado.objects.filter(estado='ACTIVO'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Timbrado'
    )

    almacen_servicios = forms.ModelChoiceField(
        required=False,
        queryset=Almacen.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Almacén para servicios',
        help_text='Seleccione el almacén del que se descontarán los productos usados en servicios'
    )

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
        
        # Establecer valores iniciales
        if self.venta:
            self.fields['tipo_documento'].initial = self.venta.tipo_documento
            self.fields['condicion'].initial = self.venta.condicion
            self.fields['timbrado'].initial = self.venta.timbrado
            
            # Configurar campos de crédito si ya existen datos
            if self.venta.condicion == '2':
                self.fields['entrega_inicial'].initial = self.venta.entrega_inicial
                self.fields['dia_vencimiento'].initial = self.venta.dia_vencimiento_cuotas
                self.fields['fecha_primer_vencimiento'].initial = self.venta.fecha_primer_vencimiento
                self.fields['numero_cuotas'].initial = self.venta.numero_cuotas or 1
                self.fields['monto_cuota'].initial = self.venta.monto_cuota or 0
        
        # Configurar almacén de servicios
        almacen_principal = Almacen.objects.filter(es_principal=True).first()
        if almacen_principal:
            self.fields['almacen_servicios'].initial = almacen_principal
        
        if self.venta and self.venta.tiene_servicios_con_inventario():
            self.fields['almacen_servicios'].required = True
            self.fields['almacen_servicios'].widget.attrs['required'] = 'required'
        else:
            self.fields['almacen_servicios'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        tipo_documento = cleaned_data.get('tipo_documento')
        condicion = cleaned_data.get('condicion')
        
        # Validar timbrado para documentos fiscales
        if tipo_documento in ['F', 'BV'] and not cleaned_data.get('timbrado'):
            self.add_error('timbrado', 'Este tipo de documento requiere timbrado')
        
        # Validaciones para ventas a crédito
        if condicion == '2':
            entrega_inicial = cleaned_data.get('entrega_inicial', 0)
            dia_vencimiento = cleaned_data.get('dia_vencimiento')
            fecha_primer_vencimiento = cleaned_data.get('fecha_primer_vencimiento')
            numero_cuotas = cleaned_data.get('numero_cuotas', 1)
            monto_cuota = cleaned_data.get('monto_cuota', 0)
            
            if entrega_inicial is None:
                self.add_error('entrega_inicial', 'Este campo es requerido para crédito')
            
            if not dia_vencimiento:
                self.add_error('dia_vencimiento', 'Debe especificar el día de vencimiento')
            elif dia_vencimiento < 1 or dia_vencimiento > 28:
                self.add_error('dia_vencimiento', 'El día debe estar entre 1 y 28')
            
            if not fecha_primer_vencimiento:
                self.add_error('fecha_primer_vencimiento', 'Debe especificar la fecha del primer vencimiento')
            elif fecha_primer_vencimiento < timezone.now().date():
                self.add_error('fecha_primer_vencimiento', 'La fecha no puede ser anterior a hoy')
            
            # Validar que la entrega inicial no supere el total
            if entrega_inicial and self.venta and entrega_inicial >= self.venta.total:
                self.add_error('entrega_inicial', 'La entrega inicial debe ser menor al total de la venta')
            
            # Validar número de cuotas y monto
            total_financiar = self.venta.total - entrega_inicial
            
            if numero_cuotas <= 0:
                self.add_error('numero_cuotas', 'El número de cuotas debe ser al menos 1')
            
            if monto_cuota <= 0:
                self.add_error('monto_cuota', 'El monto por cuota debe ser mayor a cero')
            
            # Validar coherencia entre monto y cuotas
            if monto_cuota * numero_cuotas < total_financiar:
                self.add_error('monto_cuota', 'El monto total de las cuotas no cubre el importe financiado')
        
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
        
        # Asignar datos específicos para crédito
        if condicion == '2':
            self.venta.entrega_inicial = self.cleaned_data.get('entrega_inicial', 0)
            self.venta.dia_vencimiento_cuotas = self.cleaned_data.get('dia_vencimiento', 5)
            self.venta.fecha_primer_vencimiento = self.cleaned_data.get('fecha_primer_vencimiento')
            self.venta.numero_cuotas = self.cleaned_data.get('numero_cuotas', 1)
            self.venta.monto_cuota = self.cleaned_data.get('monto_cuota', 0)
        
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
    

from .models import PagoCuota

class PagoCuotaForm(forms.ModelForm):
    class Meta:
        model = PagoCuota
        fields = ['monto', 'fecha_pago', 'tipo_pago', 'notas']
        widgets = {
            'fecha_pago': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
                },
                format='%Y-%m-%d'
            ),
            'monto': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'step': '0.01'
            }),
            'tipo_pago': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Observaciones sobre este pago'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.cuenta = kwargs.pop('cuenta', None)
        super().__init__(*args, **kwargs)
        self.fields['fecha_pago'].initial = timezone.now().date()
        
        if self.cuenta and self.cuenta.estado == 'PAGADA':
            for field in self.fields.values():
                field.widget.attrs['disabled'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        if self.cuenta and self.cuenta.estado == 'PAGADA':
            raise ValidationError("No se puede registrar pagos para una cuenta ya pagada")
        return cleaned_data