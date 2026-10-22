"""El administrador de Django queda reservado al rol de negocio ``admin``.

El acceso al sitio ya exige ``is_staff`` e ``is_active``; además se exige el rol
de negocio para que un usuario marcado como staff no herede permisos que la
aplicación no le reconoce.
"""


class SoloAdministrador:
    def _es_administrador(self, request):
        return getattr(request.user, "rol", "") == "admin"

    def has_module_permission(self, request):
        return self._es_administrador(request) and super().has_module_permission(
            request
        )

    def has_view_permission(self, request, obj=None):
        return self._es_administrador(request) and super().has_view_permission(
            request, obj
        )

    def has_add_permission(self, request):
        return self._es_administrador(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._es_administrador(request) and super().has_change_permission(
            request, obj
        )

    def has_delete_permission(self, request, obj=None):
        return self._es_administrador(request) and super().has_delete_permission(
            request, obj
        )
