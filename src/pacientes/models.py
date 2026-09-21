from django.db import models

from catalogo.models import Cliente


class Paciente(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    dni = models.CharField(max_length=15, unique=True, null=True, blank=True)
    apellidos = models.CharField(max_length=100)
    nombres = models.CharField(max_length=100)
    sexo = models.CharField(max_length=1, choices=Sexo.choices, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True, related_name="pacientes")
    observaciones = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
        ordering = ["apellidos", "nombres"]

    @property
    def nombre_completo(self):
        return f"{self.apellidos}, {self.nombres}"

    def __str__(self):
        return self.nombre_completo