# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from .models import Usuario, Sede, Dependencia
from visitantes.models import RegistroAcceso, Visitante
from datetime import datetime, timedelta
from django.db.models import Count, Q

@login_required
def dashboard(request):
    """Dashboard principal con estadísticas"""
    
    # Estadísticas del día actual
    hoy = datetime.now().date()
    visitas_hoy = RegistroAcceso.objects.filter(fecha_ingreso__date=hoy).count()
    visitas_activas = RegistroAcceso.objects.filter(estado='activo').count()
    visitantes_hoy = RegistroAcceso.objects.filter(fecha_ingreso__date=hoy).values('visitante').distinct().count()
    
    # Últimas visitas
    ultimas_visitas = RegistroAcceso.objects.select_related('visitante', 'sede', 'dependencia').order_by('-fecha_ingreso')[:10]
    
    # Visitas por sede hoy
    sedes = Sede.objects.filter(activo=True)
    visitas_por_sede = []
    for sede in sedes:
        count = RegistroAcceso.objects.filter(sede=sede, fecha_ingreso__date=hoy).count()
        if count > 0:
            visitas_por_sede.append({
                'nombre': sede.nombre,
                'visitas': count
            })
    
    # Visitas por hora hoy
    visitas_por_hora = []
    for hora in range(8, 18):  # 8 AM a 6 PM
        count = RegistroAcceso.objects.filter(
            fecha_ingreso__date=hoy,
            fecha_ingreso__hour=hora
        ).count()
        if count > 0:
            visitas_por_hora.append({
                'hora': f"{hora}:00",
                'cantidad': count
            })
    
    context = {
        'title': 'Dashboard',
        'visitas_hoy': visitas_hoy,
        'visitas_activas': visitas_activas,
        'visitantes_hoy': visitantes_hoy,
        'total_sedes': sedes.count(),
        'ultimas_visitas': ultimas_visitas,
        'visitas_por_sede': visitas_por_sede,
        'visitas_por_hora': visitas_por_hora,
    }
    return render(request, 'core/dashboard.html', context)

class CustomLoginView(LoginView):
    """Vista personalizada de login"""
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña incorrectos')
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    """Vista personalizada de logout"""
    next_page = reverse_lazy('core:login')

@login_required
def perfil_usuario(request):
    """Perfil del usuario actual"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.telefono = request.POST.get('telefono', '')
        user.save()
        messages.success(request, 'Perfil actualizado exitosamente')
        return redirect('core:perfil')
    
    return render(request, 'core/perfil.html', {'title': 'Mi Perfil'})

@login_required
def cambiar_password(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        from django.contrib.auth import update_session_auth_hash
        from django.contrib.auth.forms import PasswordChangeForm
        
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada exitosamente')
            return redirect('core:perfil')
        else:
            messages.error(request, 'Error al cambiar contraseña')
    
    return render(request, 'core/cambiar_password.html', {'title': 'Cambiar Contraseña'})

@login_required
def lista_usuarios(request):
    """Lista de usuarios del sistema (solo administradores)"""
    if not request.user.rol == 'administrador':
        messages.error(request, 'No tiene permisos para ver esta página')
        return redirect('core:dashboard')
    
    usuarios = Usuario.objects.all().order_by('-date_joined')
    
    context = {
        'usuarios': usuarios,
        'title': 'Usuarios del Sistema'
    }
    return render(request, 'core/lista_usuarios.html', context)

@login_required
def crear_usuario(request):
    """Crear nuevo usuario (solo administradores)"""
    if not request.user.rol == 'administrador':
        messages.error(request, 'No tiene permisos para ver esta página')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        rol = request.POST.get('rol')
        telefono = request.POST.get('telefono')
        
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe')
        elif Usuario.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
        else:
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                rol=rol,
                telefono=telefono
            )
            messages.success(request, f'Usuario {username} creado exitosamente')
            return redirect('core:lista_usuarios')
    
    return render(request, 'core/crear_usuario.html', {'title': 'Crear Usuario'})

@login_required
def sedes(request):
    """Gestión de sedes"""
    if not request.user.rol == 'administrador':
        messages.error(request, 'No tiene permisos para ver esta página')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo')
        direccion = request.POST.get('direccion')
        
        if Sede.objects.filter(codigo=codigo).exists():
            messages.error(request, 'El código de sede ya existe')
        else:
            Sede.objects.create(
                nombre=nombre,
                codigo=codigo,
                direccion=direccion
            )
            messages.success(request, f'Sede {nombre} creada exitosamente')
            return redirect('core:sedes')
    
    sedes_list = Sede.objects.all()
    return render(request, 'core/sedes.html', {
        'sedes': sedes_list,
        'title': 'Gestión de Sedes'
    })

@login_required
def dependencias(request):
    """Gestión de dependencias"""
    if not request.user.rol == 'administrador':
        messages.error(request, 'No tiene permisos para ver esta página')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo')
        descripcion = request.POST.get('descripcion')
        
        if Dependencia.objects.filter(codigo=codigo).exists():
            messages.error(request, 'El código de dependencia ya existe')
        else:
            Dependencia.objects.create(
                nombre=nombre,
                codigo=codigo,
                descripcion=descripcion
            )
            messages.success(request, f'Dependencia {nombre} creada exitosamente')
            return redirect('core:dependencias')
    
    dependencias_list = Dependencia.objects.all()
    return render(request, 'core/dependencias.html', {
        'dependencias': dependencias_list,
        'title': 'Gestión de Dependencias'
    })