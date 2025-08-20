from django import forms
from django.forms.widgets import DateInput
from .models import Empleado, Vacacion, Asistencia
from django.contrib.auth.models import User
from datetime import timedelta
from django.apps import apps
from .models import Eventual
from .models import Finiquito

# ---------- EmpleadoForm ----------
class DateInputWithValue(DateInput):
    input_type = 'date'

    def format_value(self, value):
        if isinstance(value, str):
            return value  # Ya está formateado, no hacer nada
        if value is not None:
            return value.strftime('%Y-%m-%d')  # Formatear si es fecha
        return ''  # Si está vacío, devolver cadena vacía


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
            'foto_identificacion_frente',
            'foto_identificacion_reverso',
 
        ]
        widgets = {
            'fecha_ingreso': DateInputWithValue()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['foto_identificacion_frente'].required = False
        self.fields['foto_identificacion_reverso'].required = False


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

        Feriado = apps.get_model('usuarios', 'Feriado')
        feriados = Feriado.objects.values_list('fecha', flat=True)
        fecha = inicio
        count = 0
        while count < dias:
            if fecha.weekday() != 6 and fecha not in feriados:
                count += 1
            fecha += timedelta(days=1)

        fecha_fin = fecha - timedelta(days=1)

        retorno = fecha
        while retorno.weekday() == 6 or retorno in feriados:
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


class EventualForm(forms.ModelForm):
    class Meta:
        model = Eventual
        fields = [
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'puesto',
            'evento',
            'encargado_evento',
            'fecha_inicio',
            'fecha_fin',
            'foto_ine',
            'foto_licencia',
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'foto_ine': forms.ClearableFileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
            'foto_licencia': forms.ClearableFileInput(attrs={'accept': 'image/*', 'capture': 'environment'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Validar que todos los campos estén llenos
        for field in self.Meta.fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'Este campo es obligatorio.')
        return cleaned_data


from django import forms
from .models import Finiquito

class FiniquitoForm(forms.ModelForm):
    class Meta:
        model = Finiquito
        fields = [
            'empleado',
            'fecha_baja',
            'horas_extra',
            'concepto_extra',
            'importe_extra',
            'concepto_descuento',
            'importe_descuento',
        ]
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-control'}),
            'fecha_baja': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'horas_extra': forms.NumberInput(attrs={'class': 'form-control'}),
            'concepto_extra': forms.TextInput(attrs={'class': 'form-control'}),
            'importe_extra': forms.NumberInput(attrs={'class': 'form-control'}),
            'concepto_descuento': forms.TextInput(attrs={'class': 'form-control'}),
            'importe_descuento': forms.NumberInput(attrs={'class': 'form-control'}),
        }
