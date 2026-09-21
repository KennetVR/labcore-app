from django.conf import settings
from django.db import models

from ordenes.models import Orden


class Pago(models.Model):
    class FormaPago(models.TextChoices):
        CONTADO = "contado", "Contado"
        BOLETA = "boleta", "Boleta"
        FACTURA = "factura", "Factura"

    orden = models.ForeignKey(Orden, on_delete=models.PROTECT, related_name="pagos")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pago = models.CharField(max_length=20, choices=FormaPago.choices, default=FormaPago.CONTADO)
    observacion = models.CharField(max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Pago {self.pk} - {self.orden.numero} (S/ {self.monto})"