from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime
from datetime import date, timedelta
import logging
logger = logging.getLogger(__name__)
from django.utils.formats import date_format
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Empleado, Asistencia
from .models import Empleado, Vacacion
from .forms import EmpleadoForm, VacacionForm, AsistenciaForm
import pandas as pd
from usuarios.calculo_horas import procesar_asistencias
from django.http import HttpResponse
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
import base64
from django.conf import settings




# --- Sesión ---
from django.urls import reverse
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'

    def get_success_url(self):
        user = self.request.user

        # Verificar si el usuario tiene un empleado asociado
        if hasattr(user, 'empleado'):
            if user.empleado.es_administrador:
                return reverse('dashboard')  # Admin
            else:
                return reverse('panel_empleado')  # Usuario común
        else:
            # Por si acaso el user no tiene un empleado asignado
            return reverse('dashboard')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

# --- Utilidades de fechas ---
def obtener_feriados(año):
    return [
        date(año, 1, 1), date(año, 2, 5), date(año, 3, 21),
        date(año, 5, 1), date(año, 9, 16), date(año, 11, 20), date(año, 12, 25)
    ]

def calcular_vacaciones(fecha_ingreso):
    hoy = timezone.now().date()
    años = hoy.year - fecha_ingreso.year
    if hoy < fecha_ingreso.replace(year=hoy.year):
        años -= 1
    if años < 1:
        return 0  # Aún no cumple el primer año

    dias = [12, 14, 16, 18, 20] + [22]*5 + [24]*5 + [26]*5 + [28]*5 + [30]*5
    return dias[años - 1] if (años - 1) < len(dias) else 32


def calcular_periodo_vacacional(fecha_inicio, dias_tomar, feriados):
    dias_efectivos = 0
    fecha_actual = fecha_inicio
    dias_vacaciones = []

    while dias_efectivos < dias_tomar:
        if fecha_actual.weekday() != 6 and fecha_actual not in feriados:
            dias_vacaciones.append(fecha_actual)
            dias_efectivos += 1
        fecha_actual += timedelta(days=1)

    fecha_fin = dias_vacaciones[-1]

    # Calcular fecha de retorno
    fecha_retorno = fecha_fin + timedelta(days=1)
    while fecha_retorno.weekday() == 6 or fecha_retorno in feriados:
        fecha_retorno += timedelta(days=1)

    return fecha_fin, fecha_retorno

# --- Dashboard ---
@login_required
def dashboard(request):
    empleado = getattr(request.user, 'empleado', None)

    return render(request, 'usuarios/dashboard.html', {
        'empleado': empleado
    })


# --- Empleados ---

@login_required
@login_required
def empleados_lista(request):
    if request.user.is_superuser:
        empleados = Empleado.objects.filter(activo=True)
    elif hasattr(request.user, 'empleado') and request.user.empleado.es_administrador:
        sucursal_admin = request.user.empleado.sucursal
        empleados = Empleado.objects.filter(activo=True, sucursal=sucursal_admin)
    else:
        empleados = Empleado.objects.none()  # Usuarios normales no ven nada

    buscar = request.GET.get('buscar', '')
    campo = request.GET.get('campo', '')

    if buscar:
        if campo == '0':
            empleados = empleados.filter(nombres__icontains=buscar)
        elif campo == '1':
            empleados = empleados.filter(puesto__icontains=buscar)
        elif campo == '2':
            empleados = empleados.filter(sucursal__icontains=buscar)
        elif campo == '3':
            empleados = empleados.filter(numero_empleado__icontains=buscar)
        elif campo == '4':
            empleados = empleados.filter(sueldo_quincenal__icontains=buscar)
        elif campo == '5':
            empleados = empleados.filter(horas_extras__icontains=buscar)
        elif campo == '6':
            empleados = empleados.filter(fecha_ingreso__icontains=buscar)

    return render(request, 'usuarios/empleados_lista.html', {
        'empleados': empleados,
        'buscar': buscar,
        'campo': campo,
    })




@login_required
def empleado_nuevo(request):
    form = EmpleadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('empleados_lista')
    return render(request, 'usuarios/empleado_form.html', {'form': form})

@login_required
def empleado_editar(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)

    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)

        # (opcional) Si el usuario no es superuser, evita que edite el campo
        if not request.user.is_superuser:
            form.fields.pop('user')

        if form.is_valid():
            form.save()
            messages.success(request, "Empleado actualizado correctamente.")
            return redirect('empleados_lista')
    else:
        form = EmpleadoForm(instance=empleado)

        if not request.user.is_superuser:
            form.fields.pop('user')

    return render(request, 'usuarios/empleado_form.html', {'form': form})


@login_required
def empleado_baja(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleado.activo = False
    empleado.save()
    return redirect('empleados_lista')

@login_required
def empleados_baja_lista(request):
    empleados = Empleado.objects.filter(activo=False).order_by('nombres')
    return render(request, 'usuarios/empleados_baja_lista.html', {'empleados': empleados})

@login_required
def empleado_recontratar(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleado.activo = True
    empleado.save()
    return redirect('empleados_baja_lista')

@login_required
def empleado_detalle(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    hoy = date.today()

    dias_vacaciones = calcular_vacaciones(empleado.fecha_ingreso)
    vacaciones_este_ano = Vacacion.objects.filter(
        empleado=empleado, fecha_inicio__year=hoy.year
    )
    feriados = obtener_feriados(hoy.year)

    dias_usados = 0
    for vac in vacaciones_este_ano:
        dia = vac.fecha_inicio
        while dia <= vac.fecha_fin:
            if dia.weekday() != 6 and dia not in feriados:
                dias_usados += 1
            dia += timedelta(days=1)

    dias_disponibles = dias_vacaciones - dias_usados
    fecha_aniversario = empleado.fecha_ingreso.replace(year=hoy.year)
    fecha_format_es = date_format(fecha_aniversario, format='j \d\e F \d\e Y', use_l10n=True)
    puede_solicitar = fecha_aniversario <= hoy
    mensaje = (
        f"Tiene derecho a {dias_vacaciones} días desde el {fecha_format_es}."
        if puede_solicitar else
        f"Le tocan {dias_vacaciones} días de vacaciones a partir del {fecha_format_es}."
)

    return render(request, 'usuarios/empleado_detalle.html', {
        'empleado': empleado,
        'dias_vacaciones': dias_vacaciones,
        'dias_disponibles': dias_disponibles,
 	'dias_usados': dias_usados, 
        'mensaje_vacaciones': mensaje,
        'puede_solicitar': puede_solicitar
    })

# --- Vacaciones ---
@login_required
def vacaciones_nueva(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id, activo=True)
    dias_disponibles = calcular_vacaciones(empleado.fecha_ingreso)

    hoy = date.today()
    feriados = obtener_feriados(hoy.year)
    vacaciones_este_ano = Vacacion.objects.filter(
        empleado=empleado,
        fecha_inicio__year=hoy.year
    )

    dias_usados = 0
    for vac in vacaciones_este_ano:
        dia = vac.fecha_inicio
        while dia <= vac.fecha_fin:
            if dia.weekday() != 6 and dia not in feriados:
                dias_usados += 1
            dia += timedelta(days=1)
    dias_disponibles -= dias_usados

    fecha_fin = None
    fecha_retorno = None
    dias_tomar = None
    error = None

    if request.method == 'POST':
        form = VacacionForm(request.POST)
        dias_tomar = int(request.POST.get('dias_a_tomar', 0))

        if form.is_valid():
            vacacion = form.save(commit=False)
            vacacion.empleado = empleado

            if dias_disponibles <= 0:
                error = "Ya no tienes días disponibles."
            elif dias_tomar <= dias_disponibles:
                fecha_inicio = vacacion.fecha_inicio
                fecha_fin, fecha_retorno = calcular_periodo_vacacional(fecha_inicio, dias_tomar, feriados)

                conflicto = Vacacion.objects.filter(
                    empleado=empleado,
                    fecha_inicio__lte=fecha_fin,
                    fecha_fin__gte=fecha_inicio
                ).exists()

                if conflicto:
                    error = "Ya existe un periodo vacacional que se cruza con estas fechas."
                else:
                    vacacion.fecha_fin = fecha_fin
                    vacacion.fecha_retorno = fecha_retorno
                    vacacion.save()
                    return redirect('vacacion_imprimir', vacacion_id=vacacion.id)

            else:
                error = "Estás solicitando más días de los que tienes disponibles."
    else:
        form = VacacionForm()

    return render(request, 'usuarios/vacacion_form.html', {
        'empleado': empleado,
        'form': form,
        'dias_disponibles': dias_disponibles,
        'fecha_fin': fecha_fin,
        'fecha_retorno': fecha_retorno,
        'dias_tomar': dias_tomar,
        'error': error,
    })

@login_required
def vacacion_confirmacion(request, vacacion_id):
    vacacion = get_object_or_404(Vacacion, id=vacacion_id)
    return render(request, 'usuarios/vacacion_confirmacion.html', {
        'vacacion': vacacion
    })

@login_required
def ficha_vacacional(request, vacacion_id):
    vacacion = get_object_or_404(Vacacion, id=vacacion_id)
    dias_corresponde = calcular_vacaciones(vacacion.empleado.fecha_ingreso)
    feriados = obtener_feriados(vacacion.fecha_inicio.year)

    dias_tomados = 0
    dia_actual = vacacion.fecha_inicio
    while dia_actual <= vacacion.fecha_fin:
        if dia_actual.weekday() != 6 and dia_actual not in feriados:
            dias_tomados += 1
        dia_actual += timedelta(days=1)

    dias_restantes = max(0, dias_corresponde - dias_tomados)

    fecha_retorno = vacacion.fecha_fin + timedelta(days=1)
    while fecha_retorno.weekday() == 6 or fecha_retorno in feriados:
        fecha_retorno += timedelta(days=1)

    return render(request, 'usuarios/vacacion_ficha.html', {
        'vacacion': vacacion,
        'dias_corresponde': dias_corresponde,
        'dias_tomados': dias_tomados,
        'dias_restantes': dias_restantes,
        'fecha_retorno': fecha_retorno,
    })

# --- Asistencia ---
@login_required
def registrar_asistencia(request):
    if request.method == 'POST':
        form = AsistenciaForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Asistencia registrada correctamente.')
                return redirect('registrar_asistencia')
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = AsistenciaForm()

    return render(request, 'usuarios/registrar_asistencia.html', {'form': form})

# --- Asignación de usuario ---
@login_required

# Copia de seguridad original
# def asignar_usuario_individual(request, empleado_id):
#    if not request.user.is_superuser:
 #       return render(request, 'usuarios/acceso_denegado.html', status=403)

#    empleado = get_object_or_404(Empleado, id=empleado_id)
#
 #   if request.method == 'POST':
  #      user_id = request.POST.get('user_id')
   #     if user_id:
    #        user = get_object_or_404(User, id=user_id)
     #       empleado.user = user
      #      empleado.save()
       #     messages.success(request, "Usuario asignado correctamente.")
        #    return redirect('empleados_lista')

#    usuarios_disponibles = User.objects.filter(empleado__isnull=True, is_active=True)
#
 #   return render(request, 'usuarios/asignar_usuario.html', {
  #      'empleado': empleado,
   #     'usuarios_disponibles': usuarios_disponibles,
    #})

def asignar_usuario_individual(request, empleado_id):
    if not request.user.is_superuser:
        return render(request, 'usuarios/acceso_denegado.html', status=403)

    empleado = get_object_or_404(Empleado, id=empleado_id)

    mensaje_credenciales = None

    if request.method == 'POST':
        if 'generar_usuario' in request.POST:
            nombres = empleado.nombres.split()[0].lower()
            apellido = empleado.apellido_paterno.lower()
            año = empleado.fecha_ingreso.year
            username = f"{nombres}{año}"
            password = f"{apellido}{año}"

            if User.objects.filter(username=username).exists():
                messages.error(request, f"El usuario '{username}' ya existe.")
            else:
                user = User.objects.create_user(username=username, password=password)
                user.first_name = empleado.nombres
                user.last_name = empleado.apellido_paterno
                user.save()

                empleado.user = user
                empleado.save()

                mensaje_credenciales = f"Usuario generado: {username} — Contraseña: {password}"
                messages.success(request, mensaje_credenciales)
                return redirect('empleados_lista')

        else:
            user_id = request.POST.get('user_id')
            if user_id:
                user = get_object_or_404(User, id=user_id)
                empleado.user = user
                empleado.save()
                messages.success(request, "Usuario asignado correctamente.")
                return redirect('empleados_lista')

    usuarios_disponibles = User.objects.filter(empleado__isnull=True, is_active=True)

    return render(request, 'usuarios/asignar_usuario.html', {
        'empleado': empleado,
        'usuarios_disponibles': usuarios_disponibles,
        'mensaje_credenciales': mensaje_credenciales
    })
 


@login_required
def vacacion_imprimir(request, vacacion_id):
    vacacion = get_object_or_404(Vacacion, id=vacacion_id)
    return render(request, 'usuarios/vacacion_imprimir.html', {
        'vacacion': vacacion
    })


@login_required
def historial_vacaciones(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    vacaciones = Vacacion.objects.filter(empleado=empleado).order_by('-fecha_inicio')

    return render(request, 'usuarios/historial_vacaciones.html', {
        'empleado': empleado,
        'vacaciones': vacaciones,
    })

from .forms import DocumentoEmpleadoForm
from .models import DocumentoEmpleado

@login_required
def documentos_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    documentos = empleado.documentos.all()  # gracias al related_name='documentos'

    if request.method == 'POST':
        form = DocumentoEmpleadoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.empleado = empleado
            documento.save()
            messages.success(request, 'Documento agregado correctamente.')
            return redirect('documentos_empleado', empleado_id=empleado.id)
    else:
        form = DocumentoEmpleadoForm()

    return render(request, 'usuarios/documentos_empleado.html', {
        'empleado': empleado,
        'documentos': documentos,
        'form': form
    })

@login_required
def eliminar_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEmpleado, id=documento_id)
    empleado_id = documento.empleado.id
    documento.delete()
    messages.success(request, 'Documento eliminado correctamente.')
    return redirect('documentos_empleado', empleado_id=empleado_id)

@login_required
def panel_empleado(request):
    empleado = get_object_or_404(Empleado, user=request.user)
    vacaciones = Vacacion.objects.filter(empleado=empleado).order_by('-fecha_inicio')

    return render(request, 'usuarios/panel_empleado.html', {
        'empleado': empleado,
        'vacaciones': vacaciones
    })


def kiosko_asistencia(request):
    return render(request, 'usuarios/kiosko_asistencia.html')

@csrf_exempt
def registrar_asistencia_kiosko(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        numero = data.get('numero_empleado')
        tipo = data.get('tipo')  # 'entrada', 'salida', 'corrido'

        try:
            empleado = Empleado.objects.get(numero_empleado=numero)
        except Empleado.DoesNotExist:
            return JsonResponse({'error': 'Empleado no encontrado'}, status=404)

         Asistencia.objects.create(
             empleado=empleado,
             tipo=tipo,
             fecha_hora=fecha_hora,  # ← usamos la hora enviada desde el navegador
             ubicacion="Kiosko",
             observaciones=""
)        

            Asistencia.objects.create(
            empleado=empleado,
            tipo=tipo,
            timestamp=timezone.now()
        )

        return JsonResponse({'mensaje': 'Asistencia registrada correctamente'})

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from .models import Vacacion
from django.conf import settings
import os
from reportlab.lib.utils import ImageReader
from datetime import datetime

def vacacion_pdf(request, vacacion_id):
    vacacion = Vacacion.objects.get(id=vacacion_id)
    empleado = vacacion.empleado

    # Validar que la fecha_retorno no sea None
    if vacacion.fecha_retorno is None:
        feriados = obtener_feriados(vacacion.fecha_inicio.year)
        fecha_retorno = vacacion.fecha_fin + timedelta(days=1)
        while fecha_retorno.weekday() == 6 or fecha_retorno in feriados:
            fecha_retorno += timedelta(days=1)
        vacacion.fecha_retorno = fecha_retorno

    # Días por ley según antigüedad
    dias_disponibles_totales = calcular_vacaciones(empleado.fecha_ingreso)
    dias_aprobados = empleado.dias_vacaciones_tomadas()
    dias_esta_solicitud = vacacion.dias_tomados
    dias_tomados_total = dias_aprobados + dias_esta_solicitud
    dias_restantes = max(0, dias_disponibles_totales - dias_tomados_total)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="solicitud_vacaciones.pdf"'
    p = canvas.Canvas(response, pagesize=LETTER)
    width, height = LETTER

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo_empresa.png')
    logger.info(f"📂 Buscando logotipo en: {logo_path}")

    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        p.drawImage(logo, x=50, y=height - 80, width=130, height=60, preserveAspectRatio=True, mask='auto')
    else:
        logger.warning("❌ LOGO NO ENCONTRADO.")

    x = 50
    y_ref = [height - 120]
    espacio = 20

    fecha_actual = datetime.today().strftime('%d/%m/%Y')
    p.setFont("Helvetica", 10)
    p.drawRightString(width - 50, height - 60, f"Generado el: {fecha_actual}")

    p.setFont("Helvetica-Bold", 14)
    p.drawString(x, y_ref[0], "SOLICITUD Y AUTORIZACIÓN DE VACACIONES")
    y_ref[0] -= 40

    p.setFont("Helvetica", 11)

    def escribir_linea(texto):
        p.drawString(x, y_ref[0], texto)
        y_ref[0] -= espacio

    escribir_linea(f"Nombre del trabajador: {empleado.nombres} {empleado.apellido_paterno} {empleado.apellido_materno}")
    escribir_linea(f"Puesto: {empleado.get_puesto_display()}")
    escribir_linea(f"Sucursal: {empleado.get_sucursal_display()}")
    escribir_linea(f"Fecha de ingreso: {empleado.fecha_ingreso.strftime('%d/%m/%Y')}")
    escribir_linea(f"Periodo vacacional: {vacacion.fecha_inicio.year}")
    escribir_linea(f"Fecha de inicio de vacaciones: {vacacion.fecha_inicio.strftime('%d/%m/%Y')}")
    escribir_linea(f"Fecha de término de vacaciones: {vacacion.fecha_fin.strftime('%d/%m/%Y')}")

    fecha_retorno_str = vacacion.fecha_retorno.strftime('%d/%m/%Y') if vacacion.fecha_retorno else '---'
    escribir_linea(f"Fecha en que debe presentarse a laborar: {fecha_retorno_str}")

    escribir_linea(f"Días de vacaciones que le corresponden por ley: {dias_disponibles_totales}")
    escribir_linea(f"Días solicitados en esta solicitud: {dias_esta_solicitud}")
    escribir_linea(f"Días ya tomados en solicitudes anteriores: {dias_aprobados}")
    escribir_linea(f"Días restantes después de esta solicitud: {dias_restantes}")
    escribir_linea(f"Motivo u observaciones: {vacacion.motivo}")

    y_ref[0] -= 40
    escribir_linea("Autorización del jefe inmediato: ___________________________")
    y_ref[0] -= 30
    escribir_linea("Nombre y firma del trabajador: ____________________________")

    p.showPage()
    p.save()
    return response

@login_required
def solicitudes_vacaciones(request):
    empleado = getattr(request.user, 'empleado', None)

    if not empleado or not empleado.es_administrador:
        return render(request, 'usuarios/acceso_denegado.html', {
            'mensaje': 'No tienes permiso para ver esta página.'
        })

    solicitudes = Vacacion.objects.filter(
        empleado__sucursal=empleado.sucursal,
        estado='pendiente' 
    ).order_by('-fecha_inicio')

    return render(request, 'usuarios/solicitudes_vacaciones.html', {
        'solicitudes': solicitudes
    })



@login_required
@require_POST
def aprobar_rechazar_solicitud(request, solicitud_id):
    empleado = getattr(request.user, 'empleado', None)

    if not empleado or not empleado.es_administrador:
        return render(request, 'usuarios/acceso_denegado.html', {
            'mensaje': 'No tienes permiso para realizar esta acción.'
        })

    solicitud = get_object_or_404(Vacacion, id=solicitud_id, empleado__sucursal=empleado.sucursal)

    accion = request.POST.get('accion')

    if accion == 'aprobar':
        solicitud.estado = 'aprobada'
        solicitud.aprobado_por = request.user
        messages.success(request, f"Solicitud de {solicitud.empleado.nombres} aprobada.")
    elif accion == 'rechazar':
        solicitud.estado = 'rechazada'
        solicitud.aprobado_por = request.user
        messages.warning(request, f"Solicitud de {solicitud.empleado.nombres} rechazada.")
    else:
        messages.error(request, "Acción no válida.")

    solicitud.save()
    return redirect('solicitudes_vacaciones')


def obtener_dataframe_asistencias():
    registros = Asistencia.objects.select_related('empleado').all()

    data = []

    for r in registros:
        data.append({
            'ID de Usuario': r.empleado.id,
            'Nombre': f"{r.empleado.nombres} {r.empleado.apellido_paterno}",
            'Fecha': r.fecha_hora.date(),
            'Tiempo': r.fecha_hora,
            'Estado': "Entrada" if r.tipo == "entrada" else "Salida",
        })

    df = pd.DataFrame(data)
    return df


@login_required
def generar_reporte_horas_extras(request):
    # Traer todas las asistencias con la info del empleado
    asistencias = Asistencia.objects.select_related('empleado').all()

    # Construir una lista de diccionarios para cada fila
    datos = []
    for asistencia in asistencias:
        datos.append({
            'ID de Usuario': asistencia.empleado.id,
            'Nombre': f"{asistencia.empleado.nombres} {asistencia.empleado.apellido_paterno}",
            'Fecha': asistencia.fecha_hora.date(),
            'Tiempo': asistencia.fecha_hora,
            'Estado': 'Entrada' if asistencia.tipo == 'entrada' else 'Salida',
        })

    # Crear el DataFrame
    df = pd.DataFrame(datos)

    # Validar si hay datos
    if df.empty:
        return HttpResponse("No hay asistencias registradas.", content_type="text/plain")

    # Procesar asistencias con tu función personalizada
    df_resultado = procesar_asistencias(df)

    # Convertir a HTML para mostrar
    html = df_resultado.to_html(index=False, justify="center", border=0, classes="table table-striped")

    return HttpResponse(f"<h2 style='text-align:center;'>Reporte de Horas Extras</h2>{html}")


def kiosko_asistencia(request):
    empleados = Empleado.objects.all().order_by('nombres')
    return render(request, 'usuarios/kiosko_asistencia.html', {'empleados': empleados})




@csrf_exempt
def registrar_asistencia_kiosko_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            numero_empleado = data.get('numero_empleado')
            tipo = data.get('tipo')

            if not numero_empleado or not tipo:
                return JsonResponse({'error': 'Faltan datos'}, status=400)

            empleado = Empleado.objects.filter(numero_empleado=numero_empleado).first()
            if not empleado:
                return JsonResponse({'error': 'Empleado no encontrado'}, status=404)

            ahora = timezone.now()
            ultima = Asistencia.objects.filter(empleado=empleado).order_by('-fecha_hora').first()

            if ultima:
                if ultima.tipo == tipo:
                    return JsonResponse({'error': f"No se puede registrar dos '{tipo}' seguidas"}, status=400)
                if (ahora - ultima.fecha_hora) < timedelta(minutes=2):
                    return JsonResponse({'error': "Debe esperar al menos 2 minutos entre registros"}, status=400)

            Asistencia.objects.create(empleado=empleado, tipo=tipo, observaciones="Registrado desde kiosko")
            return JsonResponse({'mensaje': f"{tipo.capitalize()} registrada exitosamente"})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def guardar_rostros(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            numero_empleado = data.get('numero_empleado')
            imagenes_base64 = data.get('imagenes', [])

            if not numero_empleado or not imagenes_base64:
                return JsonResponse({'error': 'Datos incompletos'}, status=400)

            # Crear carpeta si no existe
            carpeta_empleado = os.path.join(settings.MEDIA_ROOT, 'rostros_guardados', numero_empleado)
            os.makedirs(carpeta_empleado, exist_ok=True)

            # Guardar cada imagen como archivo .jpg
            for i, img_base64 in enumerate(imagenes_base64):
                img_data = base64.b64decode(img_base64.split(',')[1])
                nombre_archivo = f'rostro_{i+1}.jpg'
                ruta_completa = os.path.join(carpeta_empleado, nombre_archivo)
                with open(ruta_completa, 'wb') as f:
                    f.write(img_data)

            return JsonResponse({'mensaje': '✅ Rostros guardados exitosamente.'})
        except Exception as e:
            print("Error al guardar rostros:", str(e))
            return JsonResponse({'error': 'Ocurrió un error interno'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def validar_pin(request):
    print("📅 Inició validación PIN")

    if request.method == 'POST':
        try:
            datos = json.loads(request.body)
            numero_empleado = datos.get('numero_empleado')
            pin = datos.get('pin')
fecha_hora_str = data.get('fecha_hora')
if fecha_hora_str:
    fecha_hora = parse_datetime(fecha_hora_str)
    if fecha_hora and is_naive(fecha_hora):
        fecha_hora = make_aware(fecha_hora)
else:
    fecha_hora = timezone.now()


            tipo = datos.get('tipo')

            print("🔹 Datos recibidos:", numero_empleado, pin, tipo)

            if not numero_empleado or not pin or not tipo:
                return JsonResponse({'ok': False, 'error': 'Datos incompletos'}, status=400)

            empleado = Empleado.objects.filter(numero_empleado=numero_empleado).first()
            print("🧑 Empleado encontrado:", empleado)
            if not empleado or not empleado.user:
                print("❌ Empleado no válido o sin usuario")
                return JsonResponse({'ok': False, 'error': 'Empleado no válido'}, status=404)

            print("🔹 Username autenticando:", empleado.user.username)
            user = authenticate(username=empleado.user.username, password=pin)
            print("Resultado de authenticate:", user)

            if not user:
                return JsonResponse({'ok': False, 'error': 'PIN incorrecto'}, status=401)

            ahora = timezone.now()
            ultimo = Asistencia.objects.filter(empleado=empleado).order_by('-fecha_hora').first()

            if ultimo:
                tiempo_diferencia = (ahora - ultimo.fecha_hora).total_seconds()
                if ultimo.tipo == tipo:
                    return JsonResponse({'ok': False, 'error': f'Ya registraste una {tipo} recientemente.'})
                if tiempo_diferencia < 15:
                    return JsonResponse({'ok': False, 'error': 'Debes esperar al menos 15 segundos entre registros.'})

            Asistencia.objects.create(
                empleado=empleado,
                tipo=tipo,
                fecha_hora=ahora,
                ubicacion="Kiosko",
                observaciones="Registro por PIN desde kiosko"
            )

            return JsonResponse({'ok': True, 'mensaje': f'{tipo.capitalize()} registrada exitosamente.'})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': 'Error interno: ' + str(e)}, status=500)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

def solicitudes_empleado(request):
    return render(request, 'usuarios/solicitudes_empleado.html')
def horarios_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    asistencias = Asistencia.objects.filter(empleado=empleado).order_by('-fecha_hora')
    
    return render(request, 'usuarios/horarios_empleado.html', {
        'empleado': empleado,
        'asistencias': asistencias
    })
