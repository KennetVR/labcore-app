"""Capacidades de negocio por rol.

La autorización de la aplicación se decide por ``Usuario.rol``, no por grupos de
Django, ``is_staff`` ni ``is_superuser``. Un rol o una capacidad desconocidos se
rechazan: la política falla cerrada.
"""

ADMIN = "admin"
ENCARGADO = "encargada"

ROLES = (ADMIN, ENCARGADO)

# El encargado completa el trabajo diario del laboratorio: recepción, captura,
# validación, entrega de reportes y cobros.
CAPACIDADES_ENCARGADO = frozenset(
    {
        "pacientes.ver",
        "pacientes.editar",
        "clientes.ver",
        "clientes.editar",
        "catalogo.ver",
        "tarifas.ver",
        "ordenes.ver",
        "ordenes.editar",
        "resultados.capturar",
        "resultados.validar",
        "reportes.ver",
        "reportes.generar",
        "reportes.entregar",
        "reportes.reenviar",
        "pagos.ver",
        "pagos.registrar",
    }
)

# El administrador opera igual y además configura, autoriza y audita.
CAPACIDADES_ADMIN = CAPACIDADES_ENCARGADO | frozenset(
    {
        "pacientes.eliminar",
        "clientes.eliminar",
        "catalogo.editar",
        "tarifas.editar",
        "ordenes.eliminar",
        "ordenes.reabrir",
        "pagos.anular",
        "usuarios.gestionar",
        "auditoria.ver",
    }
)

CAPACIDADES = {
    ADMIN: CAPACIDADES_ADMIN,
    ENCARGADO: CAPACIDADES_ENCARGADO,
}


def capacidades_de(rol):
    """Capacidades vigentes del rol; un rol desconocido no tiene ninguna."""
    return CAPACIDADES.get(rol, frozenset())


def puede(rol, capacidad):
    return capacidad in capacidades_de(rol)
