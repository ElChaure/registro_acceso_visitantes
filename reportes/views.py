# reportes/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

from visitantes.models import RegistroAcceso, Visitante
from core.models import Sede, Dependencia

@login_required
def reporte_diario(request):
    """Reporte de visitas diarias"""
    # Obtener fecha del request o usar hoy
    fecha_str = request.GET.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    
    # Consultas principales
    visitas_dia = RegistroAcceso.objects.filter(fecha_ingreso__date=fecha)
    
    # Estadísticas generales
    total_visitas = visitas_dia.count()
    visitas_activas = visitas_dia.filter(estado='activo').count()
    visitas_finalizadas = visitas_dia.filter(estado='finalizado').count()
    visitantes_unicos = visitas_dia.values('visitante').distinct().count()
    
    # Visitas por hora
    visitas_por_hora = []
    for hora in range(0, 24):
        count = visitas_dia.filter(fecha_ingreso__hour=hora).count()
        if count > 0:
            visitas_por_hora.append({
                'hora': f"{hora:02d}:00",
                'cantidad': count
            })
    
    # Visitas por sede
    visitas_por_sede = []
    sedes = Sede.objects.filter(activo=True)
    for sede in sedes:
        count = visitas_dia.filter(sede=sede).count()
        if count > 0:
            visitas_por_sede.append({
                'sede': sede.nombre,
                'visitas': count,
                'porcentaje': (count / total_visitas * 100) if total_visitas > 0 else 0
            })
    
    # Visitas por dependencia
    visitas_por_dependencia = []
    dependencias = Dependencia.objects.filter(activo=True)
    for dep in dependencias:
        count = visitas_dia.filter(dependencia=dep).count()
        if count > 0:
            visitas_por_dependencia.append({
                'dependencia': dep.nombre,
                'visitas': count
            })
    
    # Últimas visitas
    ultimas_visitas = visitas_dia.select_related('visitante', 'sede', 'dependencia').order_by('-fecha_ingreso')[:20]
    
    context = {
        'title': 'Reporte Diario',
        'fecha': fecha,
        'total_visitas': total_visitas,
        'visitas_activas': visitas_activas,
        'visitas_finalizadas': visitas_finalizadas,
        'visitantes_unicos': visitantes_unicos,
        'visitas_por_hora': visitas_por_hora,
        'visitas_por_sede': visitas_por_sede,
        'visitas_por_dependencia': visitas_por_dependencia,
        'ultimas_visitas': ultimas_visitas,
    }
    return render(request, 'reportes/reporte_diario.html', context)

@login_required
def reporte_carnets(request):
    """Reporte de carnets"""
    # Filtros
    estado = request.GET.get('estado', '')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Consulta base
    carnets = RegistroAcceso.objects.all().select_related('visitante', 'sede')
    
    if estado:
        carnets = carnets.filter(estado=estado)
    if fecha_inicio:
        carnets = carnets.filter(fecha_ingreso__date__gte=fecha_inicio)
    if fecha_fin:
        carnets = carnets.filter(fecha_ingreso__date__lte=fecha_fin)
    
    # Estadísticas
    total_carnets = carnets.count()
    carnets_activos = carnets.filter(estado='activo').count()
    carnets_devueltos = carnets.filter(estado='finalizado').count()
    
    # Carnets por sede
    carnets_por_sede = []
    sedes = Sede.objects.filter(activo=True)
    for sede in sedes:
        count = carnets.filter(sede=sede).count()
        if count > 0:
            carnets_por_sede.append({
                'sede': sede.nombre,
                'total': count,
                'activos': carnets.filter(sede=sede, estado='activo').count(),
                'devueltos': carnets.filter(sede=sede, estado='finalizado').count()
            })
    
    context = {
        'title': 'Reporte de Carnets',
        'carnets': carnets.order_by('-fecha_ingreso')[:100],
        'total_carnets': total_carnets,
        'carnets_activos': carnets_activos,
        'carnets_devueltos': carnets_devueltos,
        'carnets_por_sede': carnets_por_sede,
        'estado': estado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'reportes/reporte_carnets.html', context)

@login_required
def estadisticas(request):
    """Estadísticas generales del sistema"""
    # Períodos
    hoy = timezone.now().date()
    semana_inicio = hoy - timedelta(days=7)
    mes_inicio = hoy - timedelta(days=30)
    
    # Estadísticas de hoy
    visitas_hoy = RegistroAcceso.objects.filter(fecha_ingreso__date=hoy).count()
    
    # Estadísticas de la semana
    visitas_semana = RegistroAcceso.objects.filter(fecha_ingreso__date__gte=semana_inicio).count()
    
    # Estadísticas del mes
    visitas_mes = RegistroAcceso.objects.filter(fecha_ingreso__date__gte=mes_inicio).count()
    
    # Top sedes
    top_sedes = Sede.objects.annotate(
        total_visitas=Count('registroacceso')
    ).filter(total_visitas__gt=0).order_by('-total_visitas')[:5]
    
    # Top visitantes
    top_visitantes = Visitante.objects.annotate(
        total_visitas=Count('registroacceso')
    ).filter(total_visitas__gt=0).order_by('-total_visitas')[:10]
    
    # Visitas por día (últimos 30 días)
    visitas_por_dia = []
    for i in range(30):
        fecha = hoy - timedelta(days=i)
        count = RegistroAcceso.objects.filter(fecha_ingreso__date=fecha).count()
        if count > 0 or i < 7:  # Mostrar últimos 7 días aunque sean 0
            visitas_por_dia.append({
                'fecha': fecha.strftime('%Y-%m-%d'),
                'visitas': count
            })
    
    context = {
        'title': 'Estadísticas',
        'visitas_hoy': visitas_hoy,
        'visitas_semana': visitas_semana,
        'visitas_mes': visitas_mes,
        'top_sedes': top_sedes,
        'top_visitantes': top_visitantes,
        'visitas_por_dia': reversed(visitas_por_dia),  # Orden cronológico
    }
    return render(request, 'reportes/estadisticas.html', context)

@login_required
def exportar_excel(request):
    """Exportar reporte a Excel"""
    # Obtener datos
    registros = RegistroAcceso.objects.select_related('visitante', 'sede', 'dependencia').all()
    
    # Crear DataFrame
    data = []
    for registro in registros:
        data.append({
            'Código Carnet': registro.codigo_carnet,
            'Visitante': registro.visitante.nombre_completo(),
            'Documento': registro.visitante.documento,
            'Teléfono': registro.visitante.telefono,
            'Email': registro.visitante.email,
            'Sede': registro.sede.nombre if registro.sede else '',
            'Dependencia': registro.dependencia.nombre if registro.dependencia else '',
            'Persona Solicitada': registro.persona_solicitada,
            'Fecha Ingreso': registro.fecha_ingreso.strftime('%Y-%m-%d %H:%M:%S'),
            'Fecha Salida': registro.fecha_salida.strftime('%Y-%m-%d %H:%M:%S') if registro.fecha_salida else '',
            'Estado': 'Activo' if registro.estado == 'activo' else 'Finalizado',
            'Observaciones': registro.observaciones,
        })
    
    df = pd.DataFrame(data)
    
    # Crear respuesta Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=reporte_visitas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    # Exportar a Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Visitas', index=False)
        
        # Ajustar anchos de columna
        worksheet = writer.sheets['Visitas']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return response

@login_required
def exportar_pdf(request):
    """Exportar reporte a PDF"""
    # Crear buffer para PDF
    buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elementos = []
    styles = getSampleStyleSheet()
    
    # Título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    elementos.append(Paragraph("Reporte de Control de Acceso", titulo_style))
    elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    elementos.append(Spacer(1, 20))
    
    # Obtener datos
    registros = RegistroAcceso.objects.select_related('visitante', 'sede', 'dependencia').all()[:50]
    
    # Preparar datos para la tabla
    data = [['Carnet', 'Visitante', 'Documento', 'Sede', 'Dependencia', 'Ingreso', 'Estado']]
    
    for registro in registros:
        data.append([
            registro.codigo_carnet,
            registro.visitante.nombre_completo(),
            registro.visitante.documento,
            registro.sede.nombre if registro.sede else '',
            registro.dependencia.nombre if registro.dependencia else '',
            registro.fecha_ingreso.strftime('%d/%m/%Y %H:%M'),
            'Activo' if registro.estado == 'activo' else 'Finalizado'
        ])
    
    # Crear tabla
    tabla = Table(data)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elementos.append(tabla)
    
    # Construir PDF
    doc.build(elementos)
    
    # Retornar PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=reporte_visitas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    return response