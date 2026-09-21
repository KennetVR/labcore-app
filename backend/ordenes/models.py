from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from catalogo.models import Cliente, Examen, Paquete
from pacientes.models import Paciente


class Orden(models.Model):
    class Estado(models.TextChoices):
        REGISTRADA = "registrada", "Registrada"
        EN_PROCESO = "en_proceso", "En proceso"
        RESULTADA = "resultada", "Con resultados"
        VALIDADA = "validada", "Validada"
        PDF = "pdf", "PDF generado"
        ENTREGADA = "entregada", "Entregada"

    numero = models.CharField(max_length=20, unique=True, editable=False)
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.REGISTRADA)
    solicitado_por = models.CharField(max_length=200, blank=True)
    observacion = models.TextField(blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateField(default=timezone.localdate)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "orden"
        verbose_name_plural = "ordenes"
        ordering = ["-creado"]

    def save(self, *args, **kwargs):
        if not self.numero:
            secuencia = Orden.objects.filter(fecha=self.fecha).count() + 1
            self.numero = f"{self.fecha:%Y%m%d}{secuencia:04d}"
        super().save(*args, **kwargs)

    def _tarifa(self, examen=None, paquete=None):
        from catalogo.models import TarifarioExamen, TarifarioPaquete

        if paquete:
            modelo, filtro = TarifarioPaquete, {"paquete": paquete}
        else:
            modelo, filtro = TarifarioExamen, {"examen": examen}
        candidatas = []
        qs = modelo.objects.filter(activo=True, **filtro).filter(
            Q(vigencia_desde__isnull=True) | Q(vigencia_desde__lte=self.fecha)
        )
        for t in qs.order_by("vigencia_desde"):
            if self.cliente_id and t.cliente_id == self.cliente_id:
                return t.precio
            if t.cliente_id is None and (
                t.zona_id is None or self.cliente is None or t.zona_id == self.cliente.zona_id
            ):
                candidatas.append(t.precio)
        return candidatas[-1] if candidatas else Decimal("0")

    def calcular_total(self):
        total = Decimal("0")
        for item in self.items.all():
            if item.paquete:
                total += self._tarifa(paquete=item.paquete) * item.cantidad
            else:
                total += self._tarifa(examen=item.examen) * item.cantidad
        return total.quantize(Decimal("0.01"))

    def __str__(self):
        return self.numero


class OrdenItem(models.Model):
    class Medicion(models.TextChoices):
        UNICA = "unica", "Unica"
        PRE = "pre", "Pre"
        POST = "post", "Post"

    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name="items")
    paquete = models.ForeignKey(Paquete, on_delete=models.PROTECT, null=True, blank=True)
    examen = models.ForeignKey(Examen, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    medicion = models.CharField(max_length=10, choices=Medicion.choices, default=Medicion.UNICA)
    resultado = models.CharField(max_length=100, blank=True)
    bandera = models.CharField(max_length=5, blank=True)
    importado_de = models.CharField(max_length=50, blank=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resultados_validados",
    )
    validado_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "item de orden"
        verbose_name_plural = "items de orden"
        ordering = ["orden", "id"]

    def __str__(self):
        return f"{self.orden.numero} - {self.examen.nombre}"