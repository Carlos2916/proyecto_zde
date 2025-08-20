from django.urls import path
from .import views
from .views import vacacion_pdf
from .views import CustomLoginView, CustomLogoutView, dashboard, empleados_lista, empleado_nuevo, empleado_editar, empleado_baja, empleados_baja_lista, empleado_recontratar, empleado_detalle, vacaciones_nueva, ficha_vacacional, solicitudes_empleado
from .views import asignar_usuario_individual
from .views import registrar_asistencia
from .views import vacaciones_nueva
from .views import panel_empleado
from .views import aprobar_rechazar_solicitud
from .views import guardar_rostros
from .views import validar_pin
from .views import login_admin_kiosko
from .views import (login_admin_kiosko,demo_ausencia,demo_continuos,demo_corrido,)
from .views import demo_admin




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
    path('panel-empleado/', views.panel_empleado, name='panel_empleado'),
    path('empleado/<int:empleado_id>/solicitudes/', views.solicitudes_empleado, name='solicitudes_empleado'),
    path('empleado/<int:empleado_id>/documentos/', views.documentos_empleado, name='documentos_empleado'),
    path('empleado/<int:empleado_id>/horarios/', views.horarios_empleado, name='horarios_empleado'),
    path('login_admin_kiosko/', login_admin_kiosko, name='login_admin_kiosko'),
    path('demo/ausencia/', demo_ausencia, name='demo_ausencia'),
    path('demo/continuos/', demo_continuos, name='demo_continuos'),
    path('demo/corrido/', demo_corrido, name='demo_corrido'), 
    path('demo_admin/', demo_admin, name='demo_admin'),
    path('eventuales/', views.eventuales, name='eventuales'),
    path('eventuales/nuevo/', views.eventual_nuevo, name='eventual_nuevo'),
    path('dashboard-usuario/', views.dashboard_usuario, name='dashboard_usuario'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    path('primas/', views.primas_vacacionales, name='primas_vacacionales'),
    path('primas/empleado/<int:empleado_id>/', views.primas_empleado, name='primas_empleado'),
    path('primas/marcar-pagada/<int:prima_id>/', views.marcar_prima_pagada, name='marcar_prima_pagada'),
    path('primas/documento/<int:prima_id>/', views.documento_prima, name='documento_prima'),
    path('primas/documento-pdf/<int:prima_id>/', views.documento_prima_pdf, name='documento_prima_pdf'),
    path('finiquitos/nuevo/', views.registrar_finiquito, name='registrar_finiquito'),
    path('finiquitos/', views.finiquitos_menu, name='finiquitos_menu'),
    path('finiquitos/lista/', views.finiquito_lista, name='finiquito_lista'),
    path('finiquito/nuevo/', views.finiquito_nuevo, name='finiquito_nuevo'),


]
