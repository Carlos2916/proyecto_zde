from django import forms
from django.forms.widgets import DateInput
from .models import Empleado, Vacacion, Asistencia
from django.contrib.auth.models import User
from datetime import timedelta

# ---------- EmpleadoForm ----------
class DateInputWithValue(DateInput):
    input_type = 'date'

    def format_value(self, value):
        if value is not None:
            return value.strftime('%Y-%m-%d')
        return ''

class EmpleadoForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Usuario del sistema"
    )

    class Meta:
        model = Empleado
        fields = [
            'user',
            'nombres',
            'apellido_paterno',
            'apellido_materno',
            'numero_empleado',
            'puesto',
            'sucursal',
            'sueldo_quincenal',
            'horas_extras',
            'fecha_ingreso',
            'activo',
            'es_administrador', 
        ]
        widgets = {
            'fecha_ingreso': DateInputWithValue()
        }

# ---------- VacacionForm ----------
class VacacionForm(forms.ModelForm):
    dias_a_tomar = forms.IntegerField(
        min_value=1,
        label="Días de vacaciones a tomar",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Vacacion
        fields = ['fecha_inicio', 'dias_a_tomar', 'motivo']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'fecha_inicio': 'Fecha de inicio de vacaciones',
            'motivo': 'Motivo (opcional)',
        }

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('fecha_inicio')
        dias = cleaned_data.get('dias_a_tomar')

        if not inicio or not dias:
            return cleaned_data

        feriados = Vacacion.FERIADOS_MX
        fecha = inicio
        count = 0
        while count < dias:
            if fecha.weekday() != 6 and (fecha.day, fecha.month) not in feriados:
                count += 1
            fecha += timedelta(days=1)

        fecha_fin = fecha - timedelta(days=1)

        retorno = fecha
        while retorno.weekday() == 6 or (retorno.day, retorno.month) in feriados:
            retorno += timedelta(days=1)

        cleaned_data['fecha_fin'] = fecha_fin
        cleaned_data['fecha_retorno'] = retorno

        return cleaned_data

# ---------- AsistenciaForm ----------
class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['empleado', 'tipo', 'ubicacion', 'observaciones']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

from .models import DocumentoEmpleado

class DocumentoEmpleadoForm(forms.ModelForm):
    class Meta:
        model = DocumentoEmpleado
        fields = ['nombre', 'archivo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del documento'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre del documento',
            'archivo': 'Archivo',
        }
