from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = "admin", "Administrador (gerente)"
        ENCARGADA = "encargada", "Encargada (validacion/firma)"
        AUXILIAR = "auxiliar", "Auxiliar de laboratorio"
        REPORTES = "reportes", "Asistente de reportes/facturacion"
        MUESTREO = "muestreo", "Muestreo de aguas"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.AUXILIAR)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.username