from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .admin_permisos import SoloAdministrador
from .models import Usuario


# Los roles de negocio viven en `Usuario.rol`, no en los grupos de Django.
admin.site.unregister(Group)


@admin.register(Usuario)
class UsuarioAdmin(SoloAdministrador, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)
    list_display = ("username", "get_full_name", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
