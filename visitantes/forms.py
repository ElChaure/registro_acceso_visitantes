# apps/visitantes/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Visitante, RegistroAcceso, CarnetFaltante
from core.models import Sede, Dependencia

class VisitanteForm(forms.ModelForm):
    class Meta:
        model = Visitante
        fields = ['nombre', 'apellido', 'documento', 'telefono', 'email', 'foto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el apellido'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'V-12345678'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0412-1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        if Visitante.objects.filter(documento=documento).exists():
            raise ValidationError('Este documento ya está registrado')
        return documento

class RegistroAccesoForm(forms.ModelForm):
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Seleccione una sede"
    )
    dependencia = forms.ModelChoiceField(
        queryset=Dependencia.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Seleccione una dependencia"
    )
    
    class Meta:
        model = RegistroAcceso
        fields = ['sede', 'dependencia', 'persona_solicitada', 'codigo_carnet', 'observaciones']
        widgets = {
            'persona_solicitada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la persona a visitar'}),
            'codigo_carnet': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único del carnet'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones adicionales'}),
        }
    
    def clean_codigo_carnet(self):
        codigo = self.cleaned_data.get('codigo_carnet')
        if RegistroAcceso.objects.filter(codigo_carnet=codigo, estado='activo').exists():
            raise ValidationError('Este código de carnet ya está en uso por un visitante activo')
        return codigo

class DevolucionCarnetForm(forms.Form):
    codigo_carnet = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el código del carnet',
            'autocomplete': 'off'
        }),
        label='Código de Carnet'
    )
    
    def clean_codigo_carnet(self):
        codigo = self.cleaned_data.get('codigo_carnet')
        try:
            registro = RegistroAcceso.objects.get(codigo_carnet=codigo, estado='activo')
            return codigo
        except RegistroAcceso.DoesNotExist:
            raise ValidationError('Carnet no encontrado o ya fue devuelto')

class CarnetFaltanteForm(forms.ModelForm):
    class Meta:
        model = CarnetFaltante
        fields = ['codigo_carnet', 'observaciones']
        widgets = {
            'codigo_carnet': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código del carnet faltante'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            }),
        }
    
    def clean_codigo_carnet(self):
        codigo = self.cleaned_data.get('codigo_carnet')
        try:
            registro = RegistroAcceso.objects.get(codigo_carnet=codigo, estado='activo')
            return codigo
        except RegistroAcceso.DoesNotExist:
            raise ValidationError('Carnet no encontrado o ya fue devuelto')