from django import forms
from .models import Venta, DetalleVenta, Cliente, Timbrado, ComisionVenta, ConfiguracionComision
from almacen.models import Producto, Servicio, Almacen,Stock
from caja.models import Caja
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator
from django.db.models import Q


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
    caja = forms.ModelChoiceField(
        queryset=Caja.objects.filter(estado='ABIERTA'),
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
        }),
        required=True,
        label="Caja de cobro"
    )
    
    class Meta:
        model = PagoCuota
        fields = ['monto', 'fecha_pago', 'tipo_pago', 'caja', 'notas']
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
        
        # Establecer caja inicial si la venta tiene caja asociada
        if self.cuenta and self.cuenta.venta.caja:
            self.fields['caja'].initial = self.cuenta.venta.caja
            
        if self.cuenta and self.cuenta.estado == 'PAGADA':
            for field in self.fields.values():
                field.widget.attrs['disabled'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        if self.cuenta and self.cuenta.estado == 'PAGADA':
            raise ValidationError("No se puede registrar pagos para una cuenta ya pagada")
        
        # Validar que la caja esté abierta
        caja = cleaned_data.get('caja')
        if caja and caja.estado != 'ABIERTA':
            raise ValidationError("La caja seleccionada no está abierta")
        
        return cleaned_data




from usuarios.models import PerfilUsuario
class ConfiguracionComisionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionComision
        fields = ['vendedor', 'tipo', 'porcentaje']
        widgets = {
            'vendedor': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione un vendedor'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'actualizarCampos()'
            }),
            'porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'id': 'porcentajeField'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.tipo == 'ENTREGA_INICIAL':
            self.fields['porcentaje'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        porcentaje = cleaned_data.get('porcentaje')

        if tipo == 'PORCENTAJE_VENTA' and not porcentaje:
            self.add_error('porcentaje', 'Este campo es requerido para comisión porcentual')
        
        return cleaned_data





from .models import ConfiguracionComisionCobrador


class ConfiguracionComisionCobradorForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionComisionCobrador
        fields = ['cobrador', 'porcentaje', 'activo']
        widgets = {
            'cobrador': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione un cobrador'
            }),
            'porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'id': 'porcentajeField'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtramos solo usuarios marcados como cobradores
        self.fields['cobrador'].queryset = PerfilUsuario.objects.filter(
            Q(es_cobrador=True) | Q(usuario__is_staff=True))




#INICIO SECCION DE COBROS RAPIDOS DE CUENTAS POR COBRAR
from decimal import Decimal, InvalidOperation

class BuscarClienteForm(forms.Form):
    q = forms.CharField(
        label='Buscar cliente',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre o documento del cliente',
            'class': 'form-input'
        })
    )


class ConfiguracionPagoForm(forms.Form):
    fecha_pago = forms.DateField(
        label='Fecha de pago',
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
    )
    tipo_pago = forms.ChoiceField(
        label='Tipo de pago',
        choices=PagoCuota.TIPO_PAGO_CHOICES,
        initial='EFECTIVO',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    caja = forms.ModelChoiceField(
        label='Caja',
        queryset=Caja.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    notas = forms.CharField(
        label='Notas',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-textarea',
            'placeholder': 'Observaciones sobre el pago'
        })
    )

    def __init__(self, *args, **kwargs):
        cajas_abiertas = kwargs.pop('cajas_abiertas', None)
        super().__init__(*args, **kwargs)
        if cajas_abiertas:
            self.fields['caja'].queryset = cajas_abiertas

class PagoCuentaForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'step': '0.01',
            'min': '0'
        })
    )

    def __init__(self, *args, **kwargs):
        self.cuenta = kwargs.pop('cuenta', None)
        super().__init__(*args, **kwargs)
        if self.cuenta:
            self.fields['monto'].widget.attrs['max'] = str(self.cuenta.saldo)

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if self.cuenta and monto > self.cuenta.saldo:
            raise ValidationError(f"El monto no puede ser mayor al saldo pendiente (Gs. {self.cuenta.saldo:,.2f})")
        return monto


#FIN SECCION DE COBROS RAPIDOS DE CUENTAS POR COBRAR

#INICIO SECCION DE PAGOS RAPIDOS DE COMISIONES A COBRADORES
class BuscarCobradorForm(forms.Form):
    q = forms.CharField(
        label='Buscar cobrador',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre o usuario del cobrador',
            'class': 'form-control'
        })
    )

class PagoComisionCobradorForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )

    def __init__(self, *args, **kwargs):
        self.comision = kwargs.pop('comision', None)
        super().__init__(*args, **kwargs)
        if self.comision:
            # Calcular el saldo pendiente (monto total - monto ya pagado)
            saldo_pendiente = self.comision.monto - self.comision.monto_pagado
            self.fields['monto'].initial = saldo_pendiente
            # Establecer el máximo permitido como el saldo pendiente
            self.fields['monto'].widget.attrs['max'] = str(saldo_pendiente)

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if self.comision:
            saldo_pendiente = self.comision.monto - self.comision.monto_pagado
            if monto > saldo_pendiente:
                raise ValidationError(
                    f"El monto no puede ser mayor al saldo pendiente (Gs. {saldo_pendiente:,.2f})"
                )
        return monto

#FIN SECCION DE PAGOS RAPIDOS DE COMISIONES A COBRADORES

#INICIO SECCION DE PAGOS RAPIDOS DE COMISIONES A VENDEDORES
# Añadir al final de forms.py

class BuscarVendedorForm(forms.Form):
    q = forms.CharField(
        label='Buscar vendedor',
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nombre o usuario del vendedor',
            'class': 'form-control'
        })
    )

class PagoComisionVendedorForm(forms.Form):
    monto = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        })
    )

    def __init__(self, *args, **kwargs):
        self.comision = kwargs.pop('comision', None)
        super().__init__(*args, **kwargs)
        if self.comision:
            saldo_pendiente = self.comision.saldo_pendiente
            self.fields['monto'].initial = saldo_pendiente
            self.fields['monto'].widget.attrs['max'] = str(saldo_pendiente)
            self.fields['monto'].help_text = f"Saldo pendiente: Gs. {saldo_pendiente:,.2f}"

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if self.comision and monto > self.comision.saldo_pendiente:
            raise ValidationError(
                f"El monto no puede ser mayor al saldo pendiente (Gs. {self.comision.saldo_pendiente:,.2f})"
            )
        return monto
    


#Sección de Notas de Créditos

from django import forms
from .models import NotaCredito, DetalleNotaCredito, Venta

from decimal import Decimal, InvalidOperation

class NotaCreditoForm(forms.ModelForm):
    class Meta:
        model = NotaCredito
        fields = ['venta', 'tipo', 'motivo', 'caja', 'timbrado']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3, 'minlength': 10}),
            'venta': forms.Select(attrs={'required': True}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar querysets
        self.fields['venta'].queryset = Venta.objects.filter(
            estado='FINALIZADA'
        ).select_related('cliente').order_by('-fecha')
        
        # Filtrar cajas disponibles
        if user and hasattr(user, 'perfil'):
            qs = Caja.objects.filter(estado='ABIERTA')
            if not (user.is_superuser or user.perfil.tipo_usuario == 'ADMIN'):
                qs = qs.filter(
                    Q(responsable=user.perfil) | 
                    Q(usuarios_permitidos=user.perfil)
                ).distinct()
            self.fields['caja'].queryset = qs
            if qs.count() == 1:
                self.fields['caja'].initial = qs.first()

    def clean(self):
        cleaned_data = super().clean()
        motivo = cleaned_data.get('motivo', '').strip()
        
        if len(motivo) < 10:
            self.add_error('motivo', "El motivo debe tener al menos 10 caracteres")
        
        return cleaned_data

    def clean_venta(self):
        venta = self.cleaned_data.get('venta')
        if not venta:
            raise ValidationError("Este campo es requerido")
        return venta
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            # Calcular total con redondeo a 2 decimales
            total = sum(
                Decimal(str(detalle.subtotal)).quantize(Decimal('0.01')) 
                for detalle in instance.detalles.all()
            )
            instance.total = total
            instance.save()
        
        return instance


class DetalleNotaCreditoForm(forms.ModelForm):
    class Meta:
        model = DetalleNotaCredito
        fields = ['detalle_venta', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'min': '0.001', 
                'step': '0.001',
                'pattern': '^\d+(\.\d{1,3})?$',
                'title': 'Máximo 3 decimales'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'min': '0.01', 
                'step': '0.01',
                'pattern': '^\d+(\.\d{1,2})?$',
                'title': 'Máximo 2 decimales'
            }),
        }

    def __init__(self, *args, **kwargs):
        venta = kwargs.pop('venta', None)
        super().__init__(*args, **kwargs)
        if venta:
            self.fields['detalle_venta'].queryset = venta.detalles.all()

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None:
            try:
                cantidad = Decimal(str(cantidad)).quantize(Decimal('0.001'))
            except (ValueError, InvalidOperation):
                raise ValidationError("Valor inválido para cantidad")
        return cantidad

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get('precio_unitario')
        if precio is not None:
            try:
                precio = Decimal(str(precio)).quantize(Decimal('0.01'))
            except (ValueError, InvalidOperation):
                raise ValidationError("Valor inválido para precio")
        return precio

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        precio_unitario = cleaned_data.get('precio_unitario')
        
        if cantidad and precio_unitario:
            try:
                subtotal = Decimal(str(cantidad)) * Decimal(str(precio_unitario))
                # 🔑 Redondeo a 2 decimales antes de guardar
                cleaned_data['subtotal'] = subtotal.quantize(Decimal('0.01'))
            except (ValueError, InvalidOperation):
                self.add_error(None, "Error al calcular el subtotal")
        
        return cleaned_data


