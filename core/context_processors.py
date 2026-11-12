# core/context_processors.py
from django.conf import settings

def institucion_context(request):
    return {
        'institucion_nombre': getattr(settings, 'INSTITUCION_NOMBRE', 'Mi Institución'),
        'institucion_logo': getattr(settings, 'INSTITUCION_LOGO', ''),
        'institucion_telefono': getattr(settings, 'INSTITUCION_TELEFONO', '+58 212-555-1212'),
        'institucion_email': getattr(settings, 'INSTITUCION_EMAIL', 'info@institucion.com'),
    }