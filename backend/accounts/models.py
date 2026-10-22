from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = "admin", "Administrador"
        ENCARGADO = "encargada", "Encargado"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ENCARGADO)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    def puede(self, capacidad):
        from .capacidades import puede

        return puede(self.rol, capacidad)