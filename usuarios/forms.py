from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PerfilUsuario

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email','first_name', 'last_name', 'password1', 'password2']

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'email']

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['empresa', 'sucursales', 'tipo_doc','cedula', 'telefono', 'direccion', 'tipo_usuario', 'fecha_nacimiento', 'foto_perfil', 'es_vendedor', 'es_cobrador']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cedula'].required = False  # Hacer la cédula opcional
        self.fields['telefono'].required = False  # Añade esto
        self.fields['direccion'].required = False  # Añade esto
        self.fields['empresa'].required = False
        self.fields['sucursales'].required = False
        self.fields['fecha_nacimiento'].required = False
        self.fields['foto_perfil'].required = False