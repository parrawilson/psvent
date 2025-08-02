from django import forms
from django.core.exceptions import ValidationError
from .models import Producto, Categoria, UnidadMedida, MovimientoInventario, Almacen, Stock, ConversionProducto, ComponenteConversion

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'categoria',
            'unidad_medida',
            'precio_minorista',
            'precio_mayorista',
            'tasa_iva',
            'stock_minimo',
            'imagen',
            'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del producto'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'precio_minorista': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'precio_mayorista': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'tasa_iva': forms.Select(attrs={
                'class': 'form-select'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'codigo': 'Código del Producto',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'precio_minorista': 'Precio Minorista (Gs)',
            'precio_mayorista': 'Precio Mayorista (Gs)',
            'stock_minimo': 'Stock Mínimo',
            'imagen': 'Imagen del Producto',
            'activo': 'Producto Activo'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar las categorías y unidades de medida por nombre
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nombre')
        self.fields['unidad_medida'].queryset = UnidadMedida.objects.all().order_by('nombre')
        
        # Hacer el campo código no requerido si es None
        if 'codigo' in self.fields and (not self.instance or not self.instance.codigo):
            self.fields['codigo'].required = False

    def clean(self):
        cleaned_data = super().clean()
        precio_minorista = cleaned_data.get('precio_minorista')
        precio_mayorista = cleaned_data.get('precio_mayorista')
        
        # Validar que el precio de venta no sea menor que el de compra
        if precio_minorista is not None and precio_mayorista is not None:
            if precio_mayorista > precio_minorista:
                self.add_error('precio_mayorista', 
                    'El precio mayorista no puede ser mayor al precio minorista')
        
        return cleaned_data

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:  # Solo validar si se proporciona un código
            qs = Producto.objects.filter(codigo=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Este código ya está en uso')
        return codigo
    

class CategoriaForm(forms.ModelForm):

    class Meta:
        model= Categoria
        fields= [
            'nombre',
            'descripcion',
            'activo',
        ]
        widgets= {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels={
            'nombre': 'Categoría',
            'descripcion': 'Descripción',
            'activo': 'Categoría activa'
        }

class UnidadMedidaForm(forms.ModelForm):
    class Meta:
        model= UnidadMedida
        fields =[
            'nombre',
            'abreviatura_sifen',
            'descripcion',
        ]
        widgets ={
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'

            }),
            'abreviatura_sifen': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción'
            })
        }
        labels= {
            'nombre': 'Nombre',
            'abreviatura': 'Abreviatura',
            'descripcion': 'Descripción'
        }



# forms.py (añadir al final)
class AlmacenForm(forms.ModelForm):
    class Meta:
        model = Almacen
        fields = ['nombre', 'ubicacion', 'responsable', 'sucursal', 'activo', 'es_principal']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del almacén'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ubicación física'
            }),
            'responsable': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sucursal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'es_principal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'activo': 'Almacén activo'
        }

class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['producto', 'almacen', 'cantidad', 'tipo', 'usuario', 'motivo']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'almacen': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'usuario': forms.Select(attrs={
                'class': 'form-select',
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Motivo del movimiento'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar los productos y almacenes por nombre
        self.fields['producto'].queryset = Producto.objects.filter(activo=True).order_by('nombre')
        self.fields['almacen'].queryset = Almacen.objects.filter(activo=True).order_by('nombre')
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        producto = cleaned_data.get('producto')
        almacen = cleaned_data.get('almacen')
        
        if tipo == 'SALIDA' and producto and almacen:
            stock = Stock.objects.filter(
                producto=producto,
                almacen=almacen
            ).first()
            
            if stock and cantidad > stock.cantidad:
                self.add_error('cantidad', 
                    f'Stock insuficiente. Disponible: {stock.cantidad}')

 



# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import TipoConversion, ConversionProducto, Producto, Almacen

class TipoConversionForm(forms.ModelForm):
    class Meta:
        model = TipoConversion
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ensamblaje de kits'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del tipo de conversión'
            })
        }
        labels = {
            'nombre': 'Nombre del Tipo',
            'descripcion': 'Descripción'
        }

from django import forms
from django.core.exceptions import ValidationError
from .models import ConversionProducto, Almacen, Stock

class EjecutarConversionForm(forms.Form):
    conversion = forms.ModelChoiceField(
        queryset=ConversionProducto.objects.none(),
        label="Conversión a ejecutar",
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'Seleccione conversión'
        })
    )
    almacen = forms.ModelChoiceField(
        queryset=Almacen.objects.filter(activo=True),
        label="Almacén",
        widget=forms.Select(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'Seleccione almacén'
        })
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad a convertir",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 5'
        })
    )
    motivo = forms.CharField(
        required=False,
        label="Motivo (opcional)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Ej: Preparación para venta navideña'
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar conversiones activas
        self.fields['conversion'].queryset = ConversionProducto.objects.filter(
            activo=True
        ).prefetch_related('componentes__producto')
        
        # Si el usuario no es superuser, filtrar almacenes accesibles
        if user and not user.is_superuser:
            self.fields['almacen'].queryset = Almacen.objects.filter(
                activo=True,
                responsable=user
            )

    def clean(self):
        cleaned_data = super().clean()
        conversion = cleaned_data.get('conversion')
        almacen = cleaned_data.get('almacen')
        cantidad = cleaned_data.get('cantidad')

        if not all([conversion, almacen, cantidad]):
            return cleaned_data

        # Verificar stock para todos los componentes origen
        componentes_origen = conversion.componentes.filter(tipo='ORIGEN')
        for componente in componentes_origen:
            stock = Stock.objects.filter(
                producto=componente.producto,
                almacen=almacen
            ).first()
            cantidad_necesaria = componente.cantidad * cantidad

            if not stock or stock.cantidad < cantidad_necesaria:
                self.add_error('cantidad', 
                    f'Stock insuficiente de {componente.producto.nombre}. '
                    f'Necesario: {cantidad_necesaria}, Disponible: {stock.cantidad if stock else 0}'
                )

        return cleaned_data

    def clean_cantidad(self):
        cantidad = self.cleaned_data['cantidad']
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        return cantidad

class FiltroHistorialForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        label="Desde",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    fecha_fin = forms.DateField(
        required=False,
        label="Hasta",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    tipo = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('ENSAMBLE', 'Ensamblajes'),
            ('DESENSAMBLE', 'Desensamblajes'),
            ('REVERSION', 'Reversiones')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )








class ConversionComplejaForm(forms.ModelForm):
    class Meta:
        model = ConversionProducto
        fields = ['nombre', 'tipo_conversion', 'costo_adicional', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: "Harina 50kg a paquetes"'
            }),
            'tipo_conversion': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione tipo'
            }),
            'costo_adicional': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
        }

class ComponenteConversionForm(forms.ModelForm):
    class Meta:
        model = ComponenteConversion
        fields = ['producto', 'tipo', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select select2',
                'data-placeholder': 'Seleccione producto'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            })
        }

ComponenteConversionFormSet = forms.inlineformset_factory(
    ConversionProducto,
    ComponenteConversion,
    form=ComponenteConversionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)









# forms.py
from django import forms
from .models import TrasladoProducto, DetalleTraslado

class TrasladoForm(forms.ModelForm):
    class Meta:
        model = TrasladoProducto
        fields = ['almacen_origen', 'almacen_destino', 'motivo']
        widgets = {
            'almacen_origen': forms.Select(attrs={'class': 'form-select'}),
            'almacen_destino': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            # Filtrar almacenes a los que el usuario tiene acceso
            self.fields['almacen_origen'].queryset = Almacen.objects.filter(
                activo=True,
                responsable=user
            )
            self.fields['almacen_destino'].queryset = Almacen.objects.filter(
                activo=True
            ).exclude(id__in=self.fields['almacen_origen'].queryset.values_list('id', flat=True))

class DetalleTrasladoForm(forms.ModelForm):
    class Meta:
        model = DetalleTraslado
        fields = ['producto', 'cantidad_solicitada']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control'}),
        }

DetalleTrasladoFormSet = forms.inlineformset_factory(
    TrasladoProducto,
    DetalleTraslado,
    form=DetalleTrasladoForm,
    extra=1,
    can_delete=True,
    min_num=1
)





from django import forms
from .models import Servicio, ComponenteServicio
from django.forms import inlineformset_factory


class ComponenteServicioForm(forms.ModelForm):
    class Meta:
        model = ComponenteServicio
        fields = ['producto', 'cantidad', 'observaciones']
        
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a cero")
        return cantidad


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = [
            'codigo', 'nombre', 'descripcion', 'tipo', 
            'precio', 'tasa_iva', 'duracion_estimada', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'duracion_estimada': forms.TextInput(attrs={
                'placeholder': 'HH:MM:SS',
                'help_text': 'Formato: Horas:Minutos:Segundos'
            }),
        }
        labels = {
            'duracion_estimada': 'Duración Estimada (HH:MM:SS)'
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo")
        return precio

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        
        # Validaciones adicionales pueden ir aquí
        return cleaned_data

# Formset para los componentes del servicio
ComponenteServicioFormSet = inlineformset_factory(
    Servicio,
    ComponenteServicio,
    form=ComponenteServicioForm,
    extra=1,
    can_delete=True,
    fields=('producto', 'cantidad', 'observaciones')
)

