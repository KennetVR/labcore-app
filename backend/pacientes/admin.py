from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "dni", "sexo", "cliente", "created")
    list_filter = ("sexo", "cliente")
    search_fields = ("dni", "apellidos", "nombres")

    def created(self, obj):
        return obj.creado

    created.short_description = "registrado"