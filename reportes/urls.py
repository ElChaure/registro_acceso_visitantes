# reportes/urls.py
from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.reporte_diario, name='reporte_diario'),
    path('carnets/', views.reporte_carnets, name='reporte_carnets'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
]