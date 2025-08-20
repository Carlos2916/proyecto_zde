from datetime import date
from .models import PrimaVacacional

def generar_primas_faltantes_para_empleado(empleado):
    hoy = date.today()
    
    if not empleado.fecha_ingreso:
        return

    # Paso 1: Calcular cuántos años ha trabajado el empleado
    anios_trabajados = hoy.year - empleado.fecha_ingreso.year

    # Ajustar si aún no ha cumplido el año actual
    if hoy.month < empleado.fecha_ingreso.month or (hoy.month == empleado.fecha_ingreso.month and hoy.day < empleado.fecha_ingreso.day):
        anios_trabajados -= 1

    # Paso 2: Revisar cada año cumplido
    for anio in range(1, anios_trabajados + 1):
        ya_existe = PrimaVacacional.objects.filter(empleado=empleado, anio=anio).exists()
        if not ya_existe:
            # Calcular prima vacacional básica: 6 días * 25% * sueldo diario
            try:
                sueldo_diario = float(empleado.sueldo_quincenal) / 15
            except:
                sueldo_diario = 0

            dias_legales = 6
            porcentaje_prima = 0.25
            monto = sueldo_diario * dias_legales * porcentaje_prima

            PrimaVacacional.objects.create(
                empleado=empleado,
                anio=anio,
                monto=monto,
                pagado=False
            )
