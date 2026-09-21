from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("orden", "monto", "forma_pago", "fecha", "registrado_por")
    list_filter = ("forma_pago", "fecha")
    search_fields = ("orden__numero",)