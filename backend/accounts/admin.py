from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .admin_permisos import SoloAdministrador
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(SoloAdministrador, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Rol", {"fields": ("rol",)}),)
    list_display = ("username", "get_full_name", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
