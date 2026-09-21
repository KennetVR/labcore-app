from django.contrib import admin

from .models import Reporte


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ("numero", "orden", "generado", "generado_por", "entregado_at")
    list_filter = ("enviado_a", "entregado_at")
    search_fields = ("numero", "orden__numero")