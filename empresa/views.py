from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, ListView, CreateView
from django.shortcuts import get_object_or_404, redirect
from .models import Empresa,Sucursal,PuntoExpedicion,SecuenciaDocumento,ActividadesEconomicas
from .forms import EmpresaForm, SucursalForm, PuntoExpedicionForm,SecuenciaDocumentoForm,EmpresaActividadesForm
from django.urls import reverse, reverse_lazy
from django.db import transaction

import json
from django.conf import settings
import os

class ActividadEconomicaCreateView(LoginRequiredMixin, CreateView):
    model = ActividadesEconomicas
    form_class = EmpresaActividadesForm
    template_name = 'empresas/actividad_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Cargar el JSON de actividades económicas
        file_path = os.path.join(settings.BASE_DIR, 'empresa', 'actividades_economicas.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            actividades_json = json.load(f)
        context['actividades_json'] = json.dumps(actividades_json)
        return context

    def form_valid(self, form):
        # Asigna la empresa automáticamente desde el perfil del usuario
        form.instance.empresa = self.request.user.perfil.empresa
        messages.success(self.request, "Actividad creada correctamente")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('empresa:lista_actividades')

class ActividadEconomicaUpdateView(LoginRequiredMixin, UpdateView):
    model = ActividadesEconomicas
    form_class = EmpresaActividadesForm
    template_name = 'empresas/actividad_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Cargar el JSON de actividades económicas
        file_path = os.path.join(settings.BASE_DIR, 'empresa', 'actividades_economicas.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            actividades_json = json.load(f)
        context['actividades_json'] = json.dumps(actividades_json)
        return context

    def form_valid(self, form):
        messages.success(self.request, "Actividad actualizada correctamente")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('empresa:lista_actividades')






class ActividadEconomicaListView(LoginRequiredMixin, ListView):
    model = ActividadesEconomicas
    template_name = 'empresas/actividad_list.html'
    context_object_name = 'actividades'

    def get_queryset(self):
        return ActividadesEconomicas.objects.filter(empresa=self.request.user.perfil.empresa)


class EmpresaUpdateView(LoginRequiredMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_form.html'
    
    def get_object(self):
        # Siempre edita la única empresa (o crea una si no existe)
        return Empresa.objects.first() or Empresa.objects.create(nombre="Mi Empresa")
    
    def form_valid(self, form):
        messages.success(self.request, "Datos de la empresa actualizados correctamente")
        return super().form_valid(form)
    

class SucursalCreateView(LoginRequiredMixin, CreateView):
    model = Sucursal
    form_class = SucursalForm
    template_name = 'empresas/sucursal_form.html'

    def form_valid(self, form):
        try:
            # Verifica que el usuario tenga perfil y empresa
            if hasattr(self.request.user, 'perfil') and self.request.user.perfil.empresa:
                form.instance.empresa = self.request.user.perfil.empresa
                messages.success(self.request, "Sucursal creada correctamente")
                return super().form_valid(form)
            else:
                messages.error(self.request, "No tiene una empresa asignada en su perfil")
                return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f"Error al crear sucursal: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('empresa:lista_sucursales')

    



class SucursalUpdateView(LoginRequiredMixin, UpdateView):
    model = Sucursal
    form_class = SucursalForm
    template_name = 'empresas/sucursal_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Sucursal actualizada correctamente")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('empresa:lista_sucursales')

class SucursalListView(LoginRequiredMixin, ListView):
    model = Sucursal
    template_name = 'empresas/sucursal_list.html'
    context_object_name = 'sucursales'

    def get_queryset(self):
        return Sucursal.objects.filter(empresa=self.request.user.perfil.empresa)
    


class PuntoExpedicionCreateView(LoginRequiredMixin, CreateView):
    model = PuntoExpedicion
    form_class = PuntoExpedicionForm
    template_name = 'empresas/punto_expedicion_form.html'

    def get_initial(self):
        """Establece la sucursal inicial desde la URL"""
        initial = super().get_initial()
        sucursal = get_object_or_404(Sucursal, pk=self.kwargs.get('sucursal_id'))
        initial['sucursal'] = sucursal
        return initial

    def get_context_data(self, **kwargs):
        """Añade la sucursal al contexto del template"""
        context = super().get_context_data(**kwargs)
        context['sucursal'] = self.get_initial().get('sucursal')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pasamos el usuario al formulario solo si es necesario
        if hasattr(self.request.user, 'perfil'):
            kwargs['user'] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)
        
        # Crear secuencias documentales después de crear el punto
        self.object.crear_secuencias_iniciales()
        
        messages.success(
            self.request, 
            "Punto de expedición creado exitosamente con sus secuencias documentales"
        )
        return response

    def get_success_url(self):
        return reverse('empresa:lista_puntos', kwargs={'sucursal_id': self.object.sucursal.id})


class PuntoExpedicionUpdateView(LoginRequiredMixin, UpdateView):
    model = PuntoExpedicion
    form_class = PuntoExpedicionForm
    template_name = 'empresas/punto_expedicion_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sucursal'] = self.object.sucursal
        context['sucursal_id'] = self.object.sucursal.id
        context['secuencias'] = self.object.secuencias.all()  # Añadir secuencias al contexto
        return context

    @transaction.atomic
    def form_valid(self, form):
        # Validar que el timbrado sigue siendo válido si se modifica
        if 'timbrado' in form.changed_data or 'fecha_fin_vigencia' in form.changed_data:
            if not form.instance.timbrado_valido():
                messages.warning(
                    self.request,
                    "El timbrado no está vigente según las fechas proporcionadas"
                )
        
        messages.success(self.request, "Punto de expedición actualizado exitosamente")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresa:lista_puntos', kwargs={'sucursal_id': self.object.sucursal.id})
    

class SecuenciaDocumentoUpdateView(LoginRequiredMixin, UpdateView):
    model = SecuenciaDocumento
    form_class = SecuenciaDocumentoForm
    template_name = 'empresas/secuencia_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ventas.models import Venta
        context['punto_expedicion'] = self.object.punto_expedicion
        context['documentos_emitidos'] = Venta.objects.filter(
            numero_documento__startswith=self.object.prefijo
        ).count()
        return context

    def form_valid(self, form):
        # Validación del número de secuencia
        numero_nuevo = form.cleaned_data['siguiente_numero']
        documentos_emitidos = self.get_context_data()['documentos_emitidos']
        
        if numero_nuevo <= documentos_emitidos:
            form.add_error(
                'siguiente_numero',
                f"No puede ser menor o igual a {documentos_emitidos} (documentos ya emitidos)"
            )
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        messages.success(self.request, f"Secuencia de {self.object.get_tipo_documento_display()} actualizada correctamente")
        return response

    def get_success_url(self):
        return reverse('empresa:editar_secuencias', kwargs={'pk': self.object.punto_expedicion.id})
    



class SecuenciaDocumentoListView(LoginRequiredMixin, ListView):
    model = SecuenciaDocumento
    template_name = 'empresas/secuenciadocumento_list.html'
    
    def get_queryset(self):
        return SecuenciaDocumento.objects.filter(
            punto_expedicion_id=self.kwargs['pk']
        ).order_by('tipo_documento')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['punto_expedicion'] = get_object_or_404(PuntoExpedicion, pk=self.kwargs['pk'])
        return context


class PuntoExpedicionListView(LoginRequiredMixin, ListView):
    model = PuntoExpedicion
    template_name = 'empresas/punto_expedicion_list.html'
    context_object_name = 'puntos'

    def get_queryset(self):
        sucursal_id = self.kwargs.get('sucursal_id')
        return PuntoExpedicion.objects.filter(sucursal_id=sucursal_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sucursal'] = get_object_or_404(Sucursal, pk=self.kwargs.get('sucursal_id'))
        return context




# empresa/views.py
from django.http import JsonResponse
from empresa.services.ubicaciones import UbicacionesService

def get_distritos(request):
    departamento_codigo = request.GET.get('departamento')
    ubicaciones = UbicacionesService()
    distritos = ubicaciones.get_distritos(departamento_codigo)
    return JsonResponse(distritos, safe=False)

def get_ciudades(request):
    departamento_codigo = request.GET.get('departamento')
    distrito_codigo = request.GET.get('distrito')
    ubicaciones = UbicacionesService()
    ciudades = ubicaciones.get_ciudades(departamento_codigo, distrito_codigo)
    return JsonResponse(ciudades, safe=False)

def get_barrios(request):
    departamento_codigo = request.GET.get('departamento')
    distrito_codigo = request.GET.get('distrito')
    ciudad_codigo = request.GET.get('ciudad')
    ubicaciones = UbicacionesService()
    barrios = ubicaciones.get_barrios(departamento_codigo, distrito_codigo, ciudad_codigo)
    return JsonResponse(barrios, safe=False)