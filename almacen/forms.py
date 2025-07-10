from django import forms
from django.core.exceptions import ValidationError
from .models import Producto, Categoria, UnidadMedida, MovimientoInventario, Almacen, Stock

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
            'abreviatura',
            'descripcion',
        ]
        widgets ={
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'

            }),
            'abreviatura': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Abrebiatura'
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
        fields = ['nombre', 'ubicacion', 'responsable', 'activo']
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
            'activo': forms.CheckboxInput(attrs={
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

 






