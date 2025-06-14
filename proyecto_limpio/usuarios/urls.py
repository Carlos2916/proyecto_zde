from django.urls import path
from .import views
from .views import vacacion_pdf
from .views import CustomLoginView, CustomLogoutView, dashboard, empleados_lista, empleado_nuevo, empleado_editar, empleado_baja, empleados_baja_lista, empleado_recontratar, empleado_detalle, vacaciones_nueva, ficha_vacacional
from .views import asignar_usuario_individual
from .views import registrar_asistencia
from .views import vacaciones_nueva
from .views import panel_empleado
from .views import aprobar_rechazar_solicitud
from .views import guardar_rostros
from .views import validar_pin




urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('empleados/', empleados_lista, name='empleados_lista'),
    path('empleados/nuevo/', empleado_nuevo, name='empleado_nuevo'),
    path('empleados/editar/<int:empleado_id>/', empleado_editar, name='empleado_editar'),
    path('empleados/baja/<int:empleado_id>/', empleado_baja, name='empleado_baja'),	
    path('empleados/baja/lista/', empleados_baja_lista, name='empleados_baja_lista'),
    path('empleados/recontratar/<int:empleado_id>/', empleado_recontratar, name='empleado_recontratar'),
    path('empleados/detalle/<int:empleado_id>/', empleado_detalle, name='empleado_detalle'),
    path('empleados/vacaciones/nueva/<int:empleado_id>/', vacaciones_nueva, name='vacaciones_nueva'),
    path('vacacion/ficha/<int:vacacion_id>/', views.ficha_vacacional, name='ficha_vacacional'),
    path('vacacion/imprimir/<int:vacacion_id>/', views.vacacion_imprimir, name='vacacion_imprimir'),
    path('vacacion/confirmacion/<int:vacacion_id>/', views.vacacion_confirmacion, name='vacacion_confirmacion'),
    path('empleado/<int:empleado_id>/asignar_usuario/', views.asignar_usuario_individual, name='asignar_usuario'),
    path('asistencia/', registrar_asistencia, name='registrar_asistencia'),
    path('empleado/<int:empleado_id>/vacaciones/nueva/', vacaciones_nueva, name='vacaciones_nueva'),
    path('vacacion/confirmacion/<int:vacacion_id>/', views.vacacion_confirmacion, name='vacacion_confirmacion'),
    path('empleado/<int:empleado_id>/vacaciones/historial/', views.historial_vacaciones, name='historial_vacaciones'),
    path('empleado/<int:empleado_id>/documentos/', views.documentos_empleado, name='documentos_empleado'),
    path('documento/eliminar/<int:documento_id>/', views.eliminar_documento, name='eliminar_documento'),
    path('empleado/<int:empleado_id>/panel/', views.panel_empleado, name='panel_empleado'),
    path('kiosko/', views.kiosko_asistencia, name='kiosko_asistencia'),
    path('api/kiosko/registrar/', views.registrar_asistencia_kiosko, name='registrar_asistencia_kiosko'),
    path('vacacion/pdf/<int:vacacion_id>/', vacacion_pdf, name='vacacion_pdf'),
    path('panel-empleado/', panel_empleado, name='panel_empleado'),
    path('solicitudes/<int:solicitud_id>/accion/', aprobar_rechazar_solicitud, name='aprobar_rechazar_solicitud'),
    path('solicitudes/', views.solicitudes_vacaciones, name='solicitudes_vacaciones'),
    path('reporte/horas-extras/', views.generar_reporte_horas_extras, name='reporte_horas_extras'),
    path('api/kiosko/registrar/', views.registrar_asistencia_kiosko_api, name='registrar_asistencia_kiosko_api'),
    path('api/kiosko/guardar_rostros/', guardar_rostros, name='guardar_rostros'),
    path('api/kiosko/validar_pin/', validar_pin, name='validar_pin'),




]
