from django.conf import settings
from django.db import models
from django.utils import timezone
from uuid import uuid4

from ordenes.models import Orden


class Reporte(models.Model):
    orden = models.OneToOneField(Orden, on_delete=models.CASCADE, related_name="reporte")
    numero = models.CharField(max_length=20, unique=True, editable=False)
    pdf = models.FileField(upload_to="reportes/%Y/%m", blank=True)
    codigo_qr = models.CharField(max_length=200, blank=True)
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reportes_generados",
    )
    generado = models.DateTimeField(auto_now_add=True)
    enviado_a = models.EmailField(blank=True)
    entregado_at = models.DateTimeField(null=True, blank=True)
    entregado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reportes_entregados",
    )

    class Meta:
        verbose_name = "reporte"
        verbose_name_plural = "reportes"
        ordering = ["-generado"]

    def save(self, *args, **kwargs):
        if not self.numero:
            hoy = timezone.localdate()
            secuencia = Reporte.objects.filter(generado__date=hoy).count() + 1
            self.numero = f"R{hoy:%Y%m%d}{secuencia:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero


class EnvioReporte(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ENVIADO = "enviado", "Aceptado por el servidor de correo"
        FALLIDO = "fallido", "Fallido"

    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name="envios")
    solicitud = models.UUIDField(default=uuid4, unique=True, editable=False)
    enviado_a = models.EmailField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    reenvio = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha", "-pk"]
