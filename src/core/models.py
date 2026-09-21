from django.conf import settings
from django.db import models


class Bitacora(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    accion = models.CharField(max_length=200)
    detalle = models.TextField(blank=True)
    ip = models.CharField(max_length=45, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "registro de bitacora"
        verbose_name_plural = "registros de bitacora"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} - {self.accion}"