from django.contrib import admin

from .models import (
    Cliente,
    Examen,
    Paquete,
    PaqueteExamen,
    TarifarioExamen,
    TarifarioPaquete,
    Zona,
)


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")


class PaqueteExamenInline(admin.TabularInline):
    model = PaqueteExamen
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "zona", "activo")
    list_filter = ("tipo", "zona", "activo")
    search_fields = ("nombre", "contacto")


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "area", "resultado_tipo", "unidad", "activo")
    list_filter = ("area", "activo")
    search_fields = ("codigo", "nombre")


@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "frecuencia", "activo")
    list_filter = ("frecuencia", "activo")
    search_fields = ("nombre",)
    inlines = [PaqueteExamenInline]


@admin.register(TarifarioExamen)
class TarifarioExamenAdmin(admin.ModelAdmin):
    list_display = ("examen", "precio", "zona", "cliente", "vigencia_desde", "activo")
    list_filter = ("zona", "cliente", "activo")
    autocomplete_fields = ("examen",)


@admin.register(TarifarioPaquete)
class TarifarioPaqueteAdmin(admin.ModelAdmin):
    list_display = ("paquete", "precio", "zona", "cliente", "vigencia_desde", "activo")
    list_filter = ("zona", "cliente", "activo")
    autocomplete_fields = ("paquete",)