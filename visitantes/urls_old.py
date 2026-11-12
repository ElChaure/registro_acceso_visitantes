# visitantes/urls.py
from django.urls import path
from . import views

app_name = 'visitantes'

urlpatterns = [
    path('registrar/', views.registrar_visitante, name='registrar'),
    path('devolver/', views.devolver_carnet, name='devolver'),
]