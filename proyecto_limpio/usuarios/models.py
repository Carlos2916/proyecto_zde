from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    numero_empleado = models.CharField(max_length=10, unique=True, null=True, blank=True)
    nombres = models.CharField(max_length=20)
    apellido_paterno = models.CharField(max_length=20,verbose_name='Apellido Paterno')
    apellido_materno = models.CharField(max_length=20,verbose_name='Apellido Materno')
    es_administrador = models.BooleanField(default=False, verbose_name="¿Es administrador?")


    PUESTO_OPCIONES = [
        ('administrativo', 'Administrativo'),
        ('auxiliar_general', 'Auxiliar General'),
        ('chofer', 'Chofer'),
        ('chofer_camion', 'Chofer de Camion'),
        ('encargado_de_area', 'Encargado de Area'),
        ('almacen', 'Almacén'),
        ('seguridad', 'Seguridad'),
        ('cocinera', 'Cocinero(a)'),
    ]
    puesto = models.CharField(max_length=30, choices=PUESTO_OPCIONES, default='ventas',verbose_name='Puesto')

    SUCURSAL_OPCIONES = [
        ('admin', 'Admin'),
        ('bonfil', 'Bonfil'),
        ('cabos', 'Cabos'),
        ('cedis', 'Cedis'),
        ('costa', 'Costa'),
        ('puerto', 'Puerto'),
    ]
    sucursal = models.CharField(max_length=20, choices=SUCURSAL_OPCIONES, default='centro',verbose_name='Sucursal')

    fecha_ingreso = models.DateField()

    SUELDOS_OPCIONES = [
    ('4200.00', '$4,200.00'),
    ('4500.00', '$4,500.00'),
    ('5000.00', '$5,000.00'),
    ('5500.00', '$5,500.00'),
    ('6000.00', '$6,000.00'),
    ('6500.00', '$6,500.00'),
    ]

    sueldo_quincenal = models.CharField(max_length=10, choices=SUELDOS_OPCIONES, default='4200.00',verbose_name='Sueldo Quincenal')


    HORAS_EXTRAS_OPCIONES = [
        ('60', '60'),
        ('70', '70'),
        ('80', '80'),
        ('90', '90'),
        ('100', '100'),
    ]
    horas_extras = models.CharField(max_length=10, choices=HORAS_EXTRAS_OPCIONES, default='0',verbose_name='Horas Extras')

    activo = models.BooleanField(default=True)

    correo = models.EmailField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    curp = models.CharField(max_length=18, blank=True, null=True)
    banco = models.CharField(max_length=50, blank=True, null=True)
    numero_cuenta = models.CharField(max_length=30, blank=True, null=True)
    clabe_interbancaria = models.CharField(max_length=30, blank=True, null=True)
    fecha_baja = models.DateField(blank=True, null=True)

    def dias_vacaciones_legales(self):
        hoy = date.today()
        if not self.fecha_ingreso:
            return 0
        antiguedad = hoy.year - self.fecha_ingreso.year
        if (hoy.month, hoy.day) < (self.fecha_ingreso.month, self.fecha_ingreso.day):
            antiguedad -= 1

        if antiguedad < 1:
            return 0
        elif antiguedad == 1:
            return 12
        elif antiguedad == 2:
            return 14
        elif antiguedad == 3:
            return 16
        elif antiguedad == 4:
            return 18
        elif antiguedad == 5:
            return 20
        elif 6 <= antiguedad <= 10:
            return 22
        elif 11 <= antiguedad <= 15:
            return 24
        elif 16 <= antiguedad <= 20:
            return 26
        else:
            extra = ((antiguedad - 20) // 5) * 2
            return 26 + extra 

    def save(self, *args, **kwargs):
        if self.nombres:
            self.nombres = self.nombres.title()
        if self.apellido_paterno:
            self.apellido_paterno = self.apellido_paterno.title()
        if self.apellido_materno:
            self.apellido_materno = self.apellido_materno.title()
        super().save(*args, **kwargs)
     

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno} ({'Activo' if self.activo else 'Baja'})"

    def dias_vacaciones_legales(self):
        hoy = timezone.now().date()
        antiguedad = hoy.year - self.fecha_ingreso.year
        if hoy < self.fecha_ingreso.replace(year=hoy.year):
            antiguedad -= 1
        if antiguedad < 1:
            return 6
        dias = 6 + (antiguedad - 1) * 2
        return min(dias, 12 + (antiguedad - 4)) if antiguedad <= 4 else 12 + ((antiguedad - 4) * 2)

    def dias_vacaciones_tomadas(self):
        return sum(v.dias_tomados for v in self.vacacion_set.filter(estado='aprobada'))

class DocumentoEmpleado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='documentos')
    archivo = models.FileField(upload_to='documentos_empleados/')
    nombre = models.CharField(max_length=100)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.empleado.nombres}"

class Vacacion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]

    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    fecha_retorno = models.DateField(null=True, blank=True)
    motivo = models.CharField(max_length=200)
    dias_a_tomar = models.PositiveIntegerField(verbose_name="Días a tomar")
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')
    aprobado_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="vacaciones_aprobadas")

    FERIADOS_MX = [
        (1, 1), (5, 2), (21, 3), (1, 5),
        (16, 9), (20, 11), (25, 12),
    ]

    def __str__(self):
        return f"{self.empleado.nombres} - {self.fecha_inicio} a {self.fecha_fin} ({self.estado})"

    @property
    def dias_tomados(self):
        total = 0
        dia = self.fecha_inicio
        while dia <= self.fecha_fin:
            if dia.weekday() != 6 and (dia.day, dia.month) not in self.FERIADOS_MX:
                total += 1
            dia += timedelta(days=1)
        return total

def clean(self):
    from django.core.exceptions import ValidationError

    # Validación solo si ambas fechas están completas
    if not self.fecha_inicio or not self.fecha_fin:
        return

    if self.fecha_fin < self.fecha_inicio:
        raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")

    traslape = Vacacion.objects.filter(
        empleado=self.empleado,
        fecha_inicio__lte=self.fecha_fin,
        fecha_fin__gte=self.fecha_inicio
    ).exclude(pk=self.pk)

    if traslape.exists():
        raise ValidationError("Este periodo se traslapa con otra vacación ya registrada.")


    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=[('entrada', 'Entrada'), ('salida', 'Salida')])
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.empleado.nombres} - {self.tipo} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        ahora = timezone.now()
        ultima = Asistencia.objects.filter(empleado=self.empleado).order_by('-fecha_hora').first()
        if ultima:
            if ultima.tipo == self.tipo:
                raise ValueError(f"No se puede registrar dos '{self.tipo}' seguidas para este empleado.")
            diferencia = ahora - ultima.fecha_hora
            if diferencia < timedelta(seconds=15):
                raise ValueError("Debe esperar al menos 2 minutos entre checadas.")
        super().save(*args, **kwargs)
