# apps/core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Usuario(AbstractUser):
    """Modelo de usuario extendido"""
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    cargo = models.CharField('Cargo', max_length=100, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.username}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class Sede(models.Model):
    """Modelo de sedes o puntos de acceso"""
    nombre = models.CharField('Nombre', max_length=100)
    codigo = models.CharField('Código', max_length=20, unique=True)
    direccion = models.TextField('Dirección', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class Dependencia(models.Model):
    """Modelo de dependencias o áreas"""
    nombre = models.CharField('Nombre', max_length=100)
    codigo = models.CharField('Código', max_length=20, unique=True)
    descripcion = models.TextField('Descripción', blank=True)
    activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Dependencia'
        verbose_name_plural = 'Dependencias'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Auditoria(models.Model):
    """Modelo de auditoría para registrar acciones"""
    ACCIONES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('ACCESS', 'Acceso'),
        ('RETURN', 'Devolución'),
        ('REPORT', 'Reporte'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, verbose_name='Usuario')
    accion = models.CharField('Acción', max_length=20, choices=ACCIONES)
    tabla = models.CharField('Tabla', max_length=50, blank=True)
    registro_id = models.IntegerField('ID Registro', null=True, blank=True)
    detalles = models.TextField('Detalles', blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        ordering = ['-fecha_hora']
    
    def __str__(self):
        return f"{self.fecha_hora} - {self.usuario} - {self.accion}"