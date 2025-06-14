from django.contrib import admin
from .models import Empleado, Vacacion, DocumentoEmpleado


class DocumentoEmpleadoInline(admin.TabularInline):
    model = DocumentoEmpleado
    extra = 1  # Muestra un espacio vacío para agregar un documento


class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellido_paterno', 'sucursal', 'activo', 'dias_vacaciones')
    list_filter = ('activo', 'sucursal', 'puesto')
    search_fields = ('nombres', 'apellido_paterno', 'apellido_materno', 'correo')
    inlines = [DocumentoEmpleadoInline]

    def dias_vacaciones(self, obj):
        return obj.dias_vacaciones_legales()
    dias_vacaciones.short_description = 'Vacaciones'



admin.site.register(Empleado, EmpleadoAdmin)



from .models import Asistencia

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo', 'fecha_hora', 'ubicacion')
    list_filter = ('tipo', 'fecha_hora', 'empleado__sucursal')
    search_fields = ('empleado__nombres', 'empleado__apellido_paterno')

from .models import Vacacion

@admin.register(Vacacion)
class VacacionAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_inicio', 'fecha_fin', 'estado', 'dias_tomados')
    list_filter = ('estado', 'fecha_inicio', 'fecha_fin')
    search_fields = ('empleado__nombres', 'empleado__apellido_paterno')

