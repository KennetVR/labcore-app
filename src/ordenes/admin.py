from django.contrib import admin

from .models import Orden, OrdenItem


class OrdenItemInline(admin.TabularInline):
    model = OrdenItem
    extra = 0


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ("numero", "paciente", "cliente", "estado", "fecha", "creado_por")
    list_filter = ("estado", "fecha")
    search_fields = ("numero", "paciente__dni", "paciente__apellidos")
    inlines = [OrdenItemInline]
    readonly_fields = ("numero", "creado")


@admin.register(OrdenItem)
class OrdenItemAdmin(admin.ModelAdmin):
    list_display = ("orden", "examen", "paquete", "cantidad", "medicion", "resultado", "validado_por")
    list_filter = ("medicion", "validado_por")
    search_fields = ("orden__numero", "examen__nombre")