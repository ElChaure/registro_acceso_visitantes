# visitantes/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Visitante, RegistroAcceso
from core.models import Sede, Dependencia

@login_required
def registrar_visitante(request):
    """Registrar nuevo visitante"""
    if request.method == 'POST':
        # Aquí irá la lógica de registro
        messages.success(request, 'Visitante registrado exitosamente')
        return redirect('core:dashboard')
    
    context = {
        'sedes': Sede.objects.filter(activo=True),
        'dependencias': Dependencia.objects.filter(activo=True),
        'title': 'Registrar Visitante'
    }
    return render(request, 'visitantes/registro_visitante.html', context)

@login_required
def devolver_carnet(request):
    """Devolver carnet"""
    if request.method == 'POST':
        # Aquí irá la lógica de devolución
        messages.success(request, 'Carnet devuelto exitosamente')
        return redirect('core:dashboard')
    
    return render(request, 'visitantes/devolucion_carnet.html', {'title': 'Devolver Carnet'})