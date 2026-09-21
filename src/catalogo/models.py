from django.db import models


class Zona(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "zona"
        verbose_name_plural = "zonas"

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    class Tipo(models.TextChoices):
        CLINICA = "clinica", "Clinica / Consultorio"
        DIALISIS = "dialisis", "Centro de dialisis"

    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.CLINICA)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, null=True, blank=True)
    contacto = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self):
        return self.nombre


class Examen(models.Model):
    class Area(models.TextChoices):
        SANGRE = "sangre", "Sangre"
        AGUAS = "aguas", "Aguas"

    class ResultadoTipo(models.TextChoices):
        NUMERICO = "numerico", "Numerico"
        TEXTO = "texto", "Texto"

    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=200)
    area = models.CharField(max_length=10, choices=Area.choices, default=Area.SANGRE)
    resultado_tipo = models.CharField(
        max_length=10, choices=ResultadoTipo.choices, default=ResultadoTipo.NUMERICO
    )
    unidad = models.CharField(max_length=30, blank=True)
    metodo = models.CharField(max_length=100, blank=True)
    ref_min = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ref_max = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ref_texto = models.CharField(max_length=200, blank=True)
    mide_pre_post = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "examen"
        verbose_name_plural = "examenes"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Paquete(models.Model):
    class Frecuencia(models.TextChoices):
        MENSUAL = "mensual", "Mensual"
        BIMESTRAL = "bimestral", "Bimestral"
        TRIMESTRAL = "trimestral", "Trimestral"
        SEMESTRAL = "semestral", "Semestral"

    nombre = models.CharField(max_length=100, unique=True)
    frecuencia = models.CharField(max_length=20, choices=Frecuencia.choices)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "paquete"
        verbose_name_plural = "paquetes"

    def __str__(self):
        return self.nombre


class PaqueteExamen(models.Model):
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name="examenes_compuestos")
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="paquetes_compuestos")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["paquete", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["paquete", "examen"], name="uk_paquete_examen"),
        ]
        verbose_name = "examen del paquete"
        verbose_name_plural = "examenes del paquete"

    def __str__(self):
        return f"{self.paquete.nombre}: {self.examen.nombre}"


class TarifarioExamen(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="tarifarios")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True)
    vigencia_desde = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "tarifa de examen"
        verbose_name_plural = "tarifas de examen"
        ordering = ["examen", "precio"]

    def __str__(self):
        return f"{self.examen.nombre}: S/ {self.precio}"


class TarifarioPaquete(models.Model):
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name="tarifarios")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True)
    vigencia_desde = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "tarifa de paquete"
        verbose_name_plural = "tarifas de paquete"
        ordering = ["paquete", "precio"]

    def __str__(self):
        return f"{self.paquete.nombre}: S/ {self.precio}"