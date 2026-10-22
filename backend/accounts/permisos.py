"""Permisos de DRF respaldados por las capacidades de negocio."""

from rest_framework import permissions

from .capacidades import puede


class CapacidadRequerida(permissions.BasePermission):
    """Exige la capacidad declarada para el método HTTP.

    Cada viewset define ``capacidades`` con el método como clave. Un método sin
    capacidad declarada se rechaza.
    """

    message = "No tiene permiso para esta acción."
    capacidades = {}

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method.lower() not in getattr(view, "http_method_names", []):
            # Un método no soportado no es una decisión de autorización: DRF
            # responde 405 y la inmutabilidad del recurso queda intacta.
            return True
        capacidad = self.capacidades.get(request.method)
        return bool(capacidad) and puede(getattr(user, "rol", ""), capacidad)


def permiso_por_metodo(lectura, escritura=None, borrado=None):
    """Permiso que separa lectura, escritura y borrado."""
    return type(
        "PermisoPorMetodo",
        (CapacidadRequerida,),
        {
            "capacidades": {
                "GET": lectura,
                "HEAD": lectura,
                "OPTIONS": lectura,
                "POST": escritura,
                "PUT": escritura,
                "PATCH": escritura,
                "DELETE": borrado,
            }
        },
    )
