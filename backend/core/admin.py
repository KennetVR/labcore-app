from django.contrib import admin

from accounts.admin_permisos import SoloAdministrador

from .models import Bitacora


@admin.register(Bitacora)
class BitacoraAdmin(SoloAdministrador, admin.ModelAdmin):
    list_display = ("fecha", "usuario", "accion", "ip")
    list_filter = ("accion", "fecha")
    search_fields = ("accion", "detalle", "usuario__username")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
