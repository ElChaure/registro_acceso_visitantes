# apps/visitantes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
import json
import os
from datetime import datetime, timedelta

from .models import Visitante, RegistroAcceso, CarnetFaltante
from .forms import VisitanteForm, RegistroAccesoForm, DevolucionCarnetForm, CarnetFaltanteForm
from apps.core.models import Sede, Dependencia, Auditoria
from apps.core.utils import registrar_auditoria, generar_codigo_carnet

# Decoradores personalizados
def es_operador(user):
    return user.is_authenticated and user.rol in ['operador', 'administrador']

def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'

# Vistas de visitantes
class VisitanteListView(LoginRequiredMixin, ListView):
    model = Visitante
    template_name = 'visitantes/lista_visitantes.html'
    context_object_name = 'visitantes'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(apellido__icontains=search) |
                Q(documento__icontains=search)
            )
        return queryset

@login_required
def registrar_visitante(request):
    """Vista para registrar un nuevo visitante y su acceso"""
    if request.method == 'POST':
        visitante_form = VisitanteForm(request.POST, request.FILES)
        acceso_form = RegistroAccesoForm(request.POST)
        
        if visitante_form.is_valid() and acceso_form.is_valid():
            # Guardar visitante
            visitante = visitante_form.save()
            
            # Guardar registro de acceso
            registro = acceso_form.save(commit=False)
            registro.visitante = visitante
            registro.usuario_registro = request.user
            registro.save()
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=request.user,
                accion='CREATE',
                tabla='RegistroAcceso',
                registro_id=registro.id,
                detalles=f"Visitante: {visitante.nombre_completo()}, Carnet: {registro.codigo_carnet}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Visitante registrado exitosamente. Carnet: {registro.codigo_carnet}')
            return redirect('visitantes:lista_registros_activos')
        else:
            messages.error(request, 'Error al registrar visitante. Verifique los datos.')
    else:
        visitante_form = VisitanteForm()
        acceso_form = RegistroAccesoForm()
        # Generar código de carnet automático
        acceso_form.fields['codigo_carnet'].initial = generar_codigo_carnet()
    
    context = {
        'visitante_form': visitante_form,
        'acceso_form': acceso_form,
        'title': 'Registrar Visitante'
    }
    return render(request, 'visitantes/registro_visitante.html', context)

@login_required
def devolver_carnet(request):
    """Vista para devolver carnet"""
    if request.method == 'POST':
        form = DevolucionCarnetForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_carnet']
            registro = RegistroAcceso.objects.get(codigo_carnet=codigo, estado='activo')
            
            # Registrar devolución
            registro.devolver_carnet(request.user)
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=request.user,
                accion='RETURN',
                tabla='RegistroAcceso',
                registro_id=registro.id,
                detalles=f"Carnet devuelto: {codigo}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Carnet {codigo} devuelto exitosamente')
            return redirect('visitantes:lista_registros_activos')
    else:
        form = DevolucionCarnetForm()
    
    # Obtener registros activos para mostrar
    registros_activos = RegistroAcceso.objects.filter(estado='activo').select_related('visitante', 'sede')[:10]
    
    context = {
        'form': form,
        'registros_activos': registros_activos,
        'title': 'Devolver Carnet'
    }
    return render(request, 'visitantes/devolucion_carnet.html', context)

@login_required
def lista_registros_activos(request):
    """Lista de registros de acceso activos"""
    registros = RegistroAcceso.objects.filter(estado='activo').select_related('visitante', 'sede', 'dependencia')
    
    # Filtros
    sede_id = request.GET.get('sede')
    if sede_id:
        registros = registros.filter(sede_id=sede_id)
    
    # Paginación
    paginator = Paginator(registros, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'sedes': Sede.objects.filter(activo=True),
        'title': 'Visitas Activas'
    }
    return render(request, 'visitantes/visitas_activas.html', context)

@login_required
def historial_visitas(request):
    """Historial de visitas con filtros"""
    registros = RegistroAcceso.objects.all().select_related('visitante', 'sede', 'dependencia')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    sede_id = request.GET.get('sede')
    estado = request.GET.get('estado')
    
    if fecha_inicio:
        registros = registros.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_fin:
        registros = registros.filter(fecha_ingreso__date__lte=fecha_fin)
    if sede_id:
        registros = registros.filter(sede_id=sede_id)
    if estado:
        registros = registros.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(registros, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'sedes': Sede.objects.filter(activo=True),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'title': 'Historial de Visitas'
    }
    return render(request, 'visitantes/historial.html', context)

@login_required
def carnets_faltantes(request):
    """Gestión de carnets faltantes"""
    if request.method == 'POST':
        form = CarnetFaltanteForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_carnet']
            registro = RegistroAcceso.objects.get(codigo_carnet=codigo, estado='activo')
            
            # Crear reporte de carnet faltante
            carnet_faltante = form.save(commit=False)
            carnet_faltante.registro_acceso = registro
            carnet_faltante.reportado_por = request.user
            carnet_faltante.save()
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=request.user,
                accion='REPORT',
                tabla='CarnetFaltante',
                registro_id=carnet_faltante.id,
                detalles=f"Carnet faltante reportado: {codigo}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.warning(request, f'Carnet {codigo} reportado como faltante')
            return redirect('visitantes:carnets_faltantes')
    else:
        form = CarnetFaltanteForm()
    
    # Lista de carnets faltantes
    carnets = CarnetFaltante.objects.all().select_related('registro_acceso', 'reportado_por')[:50]
    
    # Estadísticas
    estadisticas = {
        'total_reportados': CarnetFaltante.objects.count(),
        'pendientes': CarnetFaltante.objects.filter(estado='reportado').count(),
        'encontrados': CarnetFaltante.objects.filter(estado='encontrado').count(),
        'perdidos': CarnetFaltante.objects.filter(estado='perdido').count(),
    }
    
    context = {
        'form': form,
        'carnets': carnets,
        'estadisticas': estadisticas,
        'title': 'Carnets Faltantes'
    }
    return render(request, 'visitantes/carnets_faltantes.html', context)

@login_required
@require_http_methods(["POST"])
def actualizar_estado_carnet(request, pk):
    """API para actualizar estado de carnet faltante"""
    if not es_administrador(request.user):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        carnet = CarnetFaltante.objects.get(pk=pk)
        nuevo_estado = request.POST.get('estado')
        observaciones = request.POST.get('observaciones', '')
        
        if nuevo_estado in dict(CarnetFaltante.ESTADOS):
            carnet.estado = nuevo_estado
            if observaciones:
                carnet.observaciones = observaciones
            carnet.save()
            
            # Registrar auditoría
            registrar_auditoria(
                usuario=request.user,
                accion='UPDATE',
                tabla='CarnetFaltante',
                registro_id=carnet.id,
                detalles=f"Estado actualizado a: {nuevo_estado}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Estado inválido'}, status=400)
    except CarnetFaltante.DoesNotExist:
        return JsonResponse({'error': 'Carnet no encontrado'}, status=404)

@login_required
def buscar_visitante_ajax(request):
    """API para buscar visitante por documento"""
    documento = request.GET.get('documento', '')
    if documento:
        try:
            visitante = Visitante.objects.get(documento=documento)
            data = {
                'success': True,
                'id': visitante.id,
                'nombre': visitante.nombre,
                'apellido': visitante.apellido,
                'telefono': visitante.telefono,
                'email': visitante.email,
            }
            return JsonResponse(data)
        except Visitante.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Visitante no encontrado'})
    return JsonResponse({'success': False, 'error': 'Documento no proporcionado'})