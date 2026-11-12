# visitantes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.files.base import ContentFile
from .models import Visitante, RegistroAcceso, CarnetFaltante
from core.models import Sede, Dependencia
import base64
import uuid
from datetime import datetime
from .forms import CarnetFaltanteForm




def generar_codigo_carnet():
    """Genera un código único para el carnet"""
    return f"CAR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

@login_required
def registrar_visitante0(request):
    """Registrar nuevo visitante"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            documento = request.POST.get('documento')
            telefono = request.POST.get('telefono')
            email = request.POST.get('email')
            sede_id = request.POST.get('sede')
            dependencia_id = request.POST.get('dependencia')
            persona_solicitada = request.POST.get('persona_solicitada')
            observaciones = request.POST.get('observaciones')
            
            # Verificar si el visitante ya existe
            visitante, created = Visitante.objects.get_or_create(
                documento=documento,
                defaults={
                    'nombre': nombre,
                    'apellido': apellido,
                    'telefono': telefono,
                    'email': email
                }
            )
            
            if not created:
                # Actualizar datos si es necesario
                visitante.nombre = nombre
                visitante.apellido = apellido
                visitante.telefono = telefono
                visitante.email = email
                visitante.save()
            
            # Procesar foto si se subió
            if 'foto' in request.FILES:
                visitante.foto = request.FILES['foto']
                visitante.save()
            
            # Generar código de carnet
            codigo_carnet = generar_codigo_carnet()
            
            # Crear registro de acceso
            registro = RegistroAcceso.objects.create(
                visitante=visitante,
                sede_id=sede_id,
                dependencia_id=dependencia_id,
                persona_solicitada=persona_solicitada,
                codigo_carnet=codigo_carnet,
                observaciones=observaciones,
                usuario_registro=request.user
            )
            
            messages.success(request, f'Visitante registrado exitosamente. Carnet: {codigo_carnet}')
            return redirect('visitantes:registro_exitoso', registro_id=registro.id)
            
        except Exception as e:
            messages.error(request, f'Error al registrar visitante: {str(e)}')
            return redirect('visitantes:registrar')
    
    # GET - Mostrar formulario
    context = {
        'sedes': Sede.objects.filter(activo=True),
        'dependencias': Dependencia.objects.filter(activo=True),
        'title': 'Registrar Visitante'
    }
    return render(request, 'visitantes/registro_visitante.html', context)


@login_required
def registrar_visitante(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        documento = request.POST.get('documento')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        sede_id = request.POST.get('sede')
        dependencia_id = request.POST.get('dependencia')
        persona_solicitada = request.POST.get('persona_solicitada')
        observaciones = request.POST.get('observaciones')
        foto_base64 = request.POST.get('foto_base64')
        
        try:
            # Buscar o crear visitante
            visitante, created = Visitante.objects.get_or_create(
                documento=documento,
                defaults={
                    'nombre': nombre,
                    'apellido': apellido,
                    'telefono': telefono,
                    'email': email
                }
            )
            if not created:
                # Actualizar datos por si cambiaron
                visitante.nombre = nombre
                visitante.apellido = apellido
                visitante.telefono = telefono
                visitante.email = email
                visitante.save()
            
            # Procesar foto si se capturó
            if foto_base64:
                # Extraer el formato y los datos base64
                format, imgstr = foto_base64.split(';base64,')
                ext = format.split('/')[-1]  # jpeg, png, etc.
                # Generar nombre único
                filename = f"{uuid.uuid4().hex}.{ext}"
                # Decodificar y guardar
                data = base64.b64decode(imgstr)
                visitante.foto.save(filename, ContentFile(data), save=True)
            
            # Generar código de carnet
            codigo_carnet = generar_codigo_carnet()  # tu función
            
            # Crear registro de acceso
            registro = RegistroAcceso.objects.create(
                visitante=visitante,
                sede_id=sede_id,
                dependencia_id=dependencia_id,
                persona_solicitada=persona_solicitada,
                codigo_carnet=codigo_carnet,
                observaciones=observaciones,
                usuario_registro=request.user
            )
            
            messages.success(request, f'Visitante registrado exitosamente. Carnet: {codigo_carnet}')
            return redirect('visitantes:registro_exitoso', registro_id=registro.id)
            
        except Exception as e:
            messages.error(request, f'Error al registrar visitante: {str(e)}')
            return redirect('visitantes:registrar')
    
    # GET: mostrar formulario
    context = {
        'sedes': Sede.objects.filter(activo=True),
        'dependencias': Dependencia.objects.filter(activo=True),
        'title': 'Registrar Visitante'
    }
    return render(request, 'visitantes/registro_visitante.html', context)


@login_required
def registro_exitoso(request, registro_id):
    """Página de confirmación de registro"""
    registro = get_object_or_404(RegistroAcceso, id=registro_id)
    return render(request, 'visitantes/registro_exitoso.html', {
        'registro': registro,
        'title': 'Registro Exitoso'
    })

@login_required
def devolver_carnet(request):
    """Devolver carnet"""
    if request.method == 'POST':
        codigo_carnet = request.POST.get('codigo_carnet')
        
        try:
            registro = RegistroAcceso.objects.get(codigo_carnet=codigo_carnet, estado='activo')
            registro.fecha_salida = timezone.now()
            registro.estado = 'finalizado'
            registro.save()
            
            messages.success(request, f'Carnet {codigo_carnet} devuelto exitosamente')
            return redirect('visitantes:devolver')
            
        except RegistroAcceso.DoesNotExist:
            messages.error(request, 'Carnet no encontrado o ya fue devuelto')
            return redirect('visitantes:devolver')
    
    # GET - Mostrar formulario
    registros_activos = RegistroAcceso.objects.filter(estado='activo').select_related('visitante', 'sede')[:20]
    
    context = {
        'registros_activos': registros_activos,
        'title': 'Devolver Carnet'
    }
    return render(request, 'visitantes/devolucion_carnet.html', context)

@login_required
def visitas_activas(request):
    """Lista de visitas activas"""
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
    """Historial completo de visitas"""
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
def buscar_visitante(request):
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
    

@login_required
def carnets_faltantes(request):
    if request.method == 'POST':
        form = CarnetFaltanteForm(request.POST)
        if form.is_valid():
            # lógica para reportar carnet faltante
            messages.warning(request, 'Carnet reportado como faltante')
            return redirect('visitantes:carnets_faltantes')
    else:
        form = CarnetFaltanteForm()
    
    carnets = CarnetFaltante.objects.select_related('registro_acceso', 'reportado_por').all()[:50]
    context = {
        'form': form,
        'carnets': carnets,
        'title': 'Carnets Faltantes'
    }
    return render(request, 'visitantes/carnets_faltantes.html', context) 

@login_required
def lista_visitantes(request):
    """Lista todos los visitantes registrados"""
    visitantes = Visitante.objects.all().order_by('-fecha_registro')
    return render(request, 'visitantes/lista_visitantes.html', {'visitantes': visitantes, 'title': 'Lista de Visitantes'})    