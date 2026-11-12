# apps/visitantes/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from core.models import Sede, Dependencia, Usuario

class Visitante(models.Model):
    """Modelo de visitantes"""
    nombre = models.CharField('Nombre', max_length=100)
    apellido = models.CharField('Apellido', max_length=100)
    documento = models.CharField(
        'Documento de Identidad', 
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^[0-9]{6,12}$', 'Ingrese un documento válido')]
    )
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    foto = models.ImageField('Foto', upload_to='fotos_visitantes/', blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Visitante'
        verbose_name_plural = 'Visitantes'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.documento}"
    
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

class RegistroAcceso(models.Model):
    """Modelo de registros de acceso"""
    ESTADOS = [
        ('activo', 'Activo'),
        ('finalizado', 'Finalizado'),
        ('pendiente', 'Pendiente'),
    ]
    
    visitante = models.ForeignKey(Visitante, on_delete=models.PROTECT, verbose_name='Visitante')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, verbose_name='Sede')
    dependencia = models.ForeignKey(Dependencia, on_delete=models.PROTECT, verbose_name='Dependencia')
    persona_solicitada = models.CharField('Persona Solicitada', max_length=100)
    codigo_carnet = models.CharField('Código de Carnet', max_length=50, unique=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_salida = models.DateTimeField('Fecha de Salida', null=True, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='activo')
    observaciones = models.TextField('Observaciones', blank=True)
    usuario_registro = models.ForeignKey(Usuario, on_delete=models.PROTECT, verbose_name='Usuario que registró')
    fecha_salida_registro = models.DateTimeField('Fecha de Salida Registrada', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Registro de Acceso'
        verbose_name_plural = 'Registros de Acceso'
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['codigo_carnet']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_ingreso']),
        ]
    
    def __str__(self):
        return f"{self.codigo_carnet} - {self.visitante} - {self.estado}"
    
    def tiempo_estadia(self):
        """Calcula el tiempo de estadía"""
        if self.fecha_salida:
            delta = self.fecha_salida - self.fecha_ingreso
            horas = delta.total_seconds() / 3600
            return f"{horas:.1f} horas"
        return "En curso"
    
    def devolver_carnet(self, usuario):
        """Devuelve el carnet"""
        self.fecha_salida = timezone.now()
        self.estado = 'finalizado'
        self.fecha_salida_registro = timezone.now()
        self.save()

class CarnetFaltante(models.Model):
    """Modelo de carnets reportados como faltantes"""
    ESTADOS = [
        ('reportado', 'Reportado'),
        ('encontrado', 'Encontrado'),
        ('perdido', 'Perdido'),
    ]
    
    registro_acceso = models.ForeignKey(RegistroAcceso, on_delete=models.CASCADE, verbose_name='Registro de Acceso')
    codigo_carnet = models.CharField('Código de Carnet', max_length=50)
    fecha_reporte = models.DateTimeField(auto_now_add=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADOS, default='reportado')
    observaciones = models.TextField('Observaciones', blank=True)
    reportado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, verbose_name='Reportado por')
    
    class Meta:
        verbose_name = 'Carnet Faltante'
        verbose_name_plural = 'Carnets Faltantes'
        ordering = ['-fecha_reporte']
    
    def __str__(self):
        return f"{self.codigo_carnet} - {self.estado}"