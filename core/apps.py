# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'  # Nombre simple, sin 'apps.'
    verbose_name = 'Núcleo del Sistema'