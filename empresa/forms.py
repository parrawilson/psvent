from django import forms
from django.shortcuts import get_object_or_404
from .models import Empresa, Sucursal, PuntoExpedicion,SecuenciaDocumento, ActividadesEconomicas

from empresa.services.ubicaciones import UbicacionesService

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar opciones iniciales
        ubicaciones = UbicacionesService()
        self.fields['departamento_codigo'].choices = self._get_departamento_choices()
        
        # Configurar campos vacíos inicialmente
        self.fields['distrito_codigo'].choices = [('', '---------')]
        self.fields['ciudad_codigo'].choices = [('', '---------')]
        self.fields['barrio_codigo'].choices = [('', '---------')]
        
        # Si hay una instancia, cargar los valores correspondientes
        if self.instance.pk:
            if self.instance.departamento_codigo:
                self.fields['distrito_codigo'].choices = self._get_distrito_choices(
                    self.instance.departamento_codigo
                )
            if self.instance.distrito_codigo:
                self.fields['ciudad_codigo'].choices = self._get_ciudad_choices(
                    self.instance.departamento_codigo,
                    self.instance.distrito_codigo
                )
            if self.instance.ciudad_codigo:
                self.fields['barrio_codigo'].choices = self._get_barrio_choices(
                    self.instance.departamento_codigo,
                    self.instance.distrito_codigo,
                    self.instance.ciudad_codigo
                )
    
    def _get_departamento_choices(self):
        ubicaciones = UbicacionesService()
        departamentos = ubicaciones.get_departamentos()
        return [('', '---------')] + [(d['codigo'], d['nombre']) for d in departamentos]
    
    def _get_distrito_choices(self, departamento_codigo):
        ubicaciones = UbicacionesService()
        distritos = ubicaciones.get_distritos(departamento_codigo)
        return [('', '---------')] + [(d['codigo'], d['nombre']) for d in distritos]
    
    def _get_ciudad_choices(self, departamento_codigo, distrito_codigo):
        ubicaciones = UbicacionesService()
        ciudades = ubicaciones.get_ciudades(departamento_codigo, distrito_codigo)
        return [('', '---------')] + [(c['codigo'], c['nombre']) for c in ciudades]
    
    def _get_barrio_choices(self, departamento_codigo, distrito_codigo, ciudad_codigo):
        ubicaciones = UbicacionesService()
        barrios = ubicaciones.get_barrios(departamento_codigo, distrito_codigo, ciudad_codigo)
        return [('', '---------')] + [(b['codigo'], b['nombre']) for b in barrios]

class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ['nombre', 'codigo', 'direccion', 'telefono', 'es_principal', 'activa']
        widgets = {
            'direccion': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'pattern': '[0-9]{3}',
                'title': '3 dígitos numéricos'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
        }


class PuntoExpedicionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Extraemos el parámetro user si existe
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtramos las sucursales disponibles según la empresa del usuario
        if self.user and hasattr(self.user, 'perfil') and self.user.perfil.empresa:
            self.fields['sucursal'].queryset = Sucursal.objects.filter(
                empresa=self.user.perfil.empresa
            )

    class Meta:
        model = PuntoExpedicion
        fields = ['sucursal', 'codigo', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-input',
                'pattern': '[0-9]{3}',
                'title': '3 dígitos numéricos'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Caja Principal'
            }),
            'sucursal': forms.Select(attrs={
                'class': 'form-select'
            })
        }



class SecuenciaDocumentoForm(forms.ModelForm):
    prefijo_display = forms.CharField(
        label="Prefijo",
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input bg-gray-100 rounded-md',
        })
    )

    class Meta:
        model = SecuenciaDocumento
        fields = ['siguiente_numero', 'activo']
        widgets = {
            'siguiente_numero': forms.NumberInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': '1',
                'step': '1'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['prefijo_display'].initial = self.instance.prefijo
        else:
            self.fields['prefijo_display'].initial = "Se generará automáticamente"

    def clean_siguiente_numero(self):
        numero = self.cleaned_data['siguiente_numero']
        if numero < 1:
            raise forms.ValidationError("El número debe ser mayor o igual a 1")
        return numero

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Solo actualizar el siguiente número y estado activo
        if commit:
            instance.save(update_fields=['siguiente_numero', 'activo'])
        return instance



class EmpresaActividadesForm(forms.ModelForm):
    class Meta:
        model = ActividadesEconomicas
        fields = ['codigo', 'descripcion', 'es_principal']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500',
                'title': '3 dígitos numéricos'
            }),
        }