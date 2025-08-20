from django.apps import apps
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
        ('encargado', 'Encargado'),
        ('vendedor', 'Vendedor'),
        ('auxiliar_general', 'Auxiliar General'),
        ('chofer', 'Chofer'),
        ('chofer_camion', 'Chofer de Camion'),
        ('encargado_de_area', 'Encargado de Area'),
        ('encargado_de_almacen', 'Almacén'),
        ('seguridad', 'Seguridad'),
        ('cocinera', 'Cocinero(a)'),
        ('supervisor_montajes', 'Supervisor de Montaje'),
    ]
    puesto = models.CharField(max_length=30, choices=PUESTO_OPCIONES, default='ventas',verbose_name='Puesto')

    SUCURSAL_OPCIONES = [
        ('chichen', 'Chichen'),
        ('bonfil', 'Bonfil'),
        ('cabos', 'Cabos'),
        ('cedis', 'Cedis'),
        ('costa', 'Costa'),
        ('puerto', 'Puerto'),
        ('ventas', 'Ventas'),
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
    ('7000.00', '$7,500.00'),
    ('8000.00', '$8,500.00'),
    ('9000.00', '$9,500.00'),
    ('10000.00', '$10,000.00'),
    ('11000.00', '$11,000.00'),
    ('12500.00', '$12,500.00'),
    ('15000.00', '$15,000.00'),
    ('20000.00', '$20,000.00'),
    ('30000.00', '$30,000.00'),
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


    foto_identificacion_frente = models.ImageField(
        upload_to='empleados_identificaciones/',
        null=False,   # cambia a True temporalmente
        blank=False,  # cambia a True temporalmente
        verbose_name='Foto Identificación Frente'
    )

    foto_identificacion_reverso = models.ImageField(
        upload_to='empleados_identificaciones/',
        null=False,   # cambia a True temporalmente y volver a False cuando ya todos tengan foto
        blank=False,  # cambia a True temporalmente y volver a False cuando ya todos tengan foto
        verbose_name='Foto Identificación Reverso'
    )





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

    @property
    def dias_vacaciones_legales(self):
        hoy = timezone.now().date()
         
        # Prevención de error si la fecha es 29 de febrero y el año actual no es bisiesto
        try:
            aniversario = self.fecha_ingreso.replace(year=hoy.year)
        except ValueError:
            aniversario = self.fecha_ingreso.replace(year=hoy.year, day=28)
         
        antiguedad = hoy.year - self.fecha_ingreso.year
        if hoy < aniversario:
            antiguedad -= 1
         
        if antiguedad < 1:
            return 6  # año 1
         
        dias = 6 + (antiguedad - 1) * 2
        return min(dias, 12 + ((antiguedad - 4) * 2)) if antiguedad > 4 else dias


    def dias_vacaciones_tomadas(self):
        return sum(v.dias_tomados for v in self.vacacion_set.filter(estado='aprobada'))


class PrimaVacacional(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    anio = models.PositiveIntegerField(verbose_name="Año cumplido")
    fecha_generada = models.DateField(auto_now_add=True)
    fecha_pago = models.DateField(null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    pagado = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('empleado', 'anio')  # Evita duplicados

    def __str__(self):
        return f"{self.empleado} - Año {self.anio} - {'Pagado' if self.pagado else 'Pendiente'}"





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


    def __str__(self):
        return f"{self.empleado.nombres} - {self.fecha_inicio} a {self.fecha_fin} ({self.estado})"

    @property
    def dias_tomados(self):
        Feriado = apps.get_model('usuarios', 'Feriado')
        feriados = Feriado.objects.values_list('fecha', flat=True)
        total = 0
        dia = self.fecha_inicio
        while dia <= self.fecha_fin:
            if dia.weekday() != 6 and dia not in feriados:
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

class Feriado(models.Model):
    fecha = models.DateField(unique=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} - {self.fecha.strftime('%d/%m/%Y')}"


class Eventual(models.Model):
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    puesto = models.CharField(max_length=100)
    evento = models.CharField(max_length=200)
    encargado_evento = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    foto_ine = models.ImageField(upload_to='eventuales/ine/')
    foto_licencia = models.ImageField(upload_to='eventuales/licencia/')

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"




ESTADOS_FINIQUITO = (
    ('pendiente', 'Pendiente'),
    ('pagado', 'Pagado'),
    ('firmado', 'Firmado'),
)

class Finiquito(models.Model):
    # Campos existentes
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha_baja = models.DateField()
    horas_extra = models.IntegerField(default=0)

    # Campos opcionales
    concepto_extra = models.CharField(max_length=255, blank=True, null=True)
    importe_extra = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    concepto_descuento = models.CharField(max_length=255, blank=True, null=True)
    importe_descuento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # NUEVO campo estado
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADOS, default='pendiente')

    def total_neto(self):
        base = 0
        if self.importe_extra:
            base += self.importe_extra
        if self.importe_descuento:
            base -= self.importe_descuento
        return base

    def __str__(self):
        return f'Finiquito de {self.empleado} - {self.fecha_baja}'
