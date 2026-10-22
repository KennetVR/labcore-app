"""Política de dos roles: capacidades y modelo de usuario."""

import pytest
from django.contrib.auth import get_user_model

from accounts.capacidades import ADMIN, ENCARGADO, capacidades_de, puede

CAPACIDADES_DEL_ENCARGADO = [
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
]

CAPACIDADES_SOLO_ADMIN = [
    "pacientes.eliminar",
    "clientes.eliminar",
    "catalogo.editar",
    "tarifas.editar",
    "ordenes.eliminar",
    "ordenes.reabrir",
    "pagos.anular",
    "usuarios.gestionar",
    "auditoria.ver",
]


def test_solo_existen_dos_roles():
    assert [clave for clave, _ in get_user_model().Rol.choices] == [ADMIN, ENCARGADO]


def test_el_rol_por_defecto_es_el_encargado():
    usuario = get_user_model()(username="nuevo")

    assert usuario.rol == ENCARGADO


@pytest.mark.parametrize("capacidad", CAPACIDADES_DEL_ENCARGADO)
def test_el_encargado_atiende_la_operacion_diaria(capacidad):
    assert puede(ENCARGADO, capacidad)


@pytest.mark.parametrize("capacidad", CAPACIDADES_SOLO_ADMIN)
def test_el_encargado_no_administra(capacidad):
    assert not puede(ENCARGADO, capacidad)


@pytest.mark.parametrize("capacidad", CAPACIDADES_DEL_ENCARGADO + CAPACIDADES_SOLO_ADMIN)
def test_el_administrador_puede_todo(capacidad):
    assert puede(ADMIN, capacidad)


@pytest.mark.parametrize("rol", ["auxiliar", "reportes", "muestreo", "", None])
def test_un_rol_fuera_de_la_politica_falla_cerrado(rol):
    assert capacidades_de(rol) == frozenset()
    assert not puede(rol, "ordenes.ver")
    assert not puede(rol, "pagos.registrar")


def test_el_usuario_expone_su_capacidad():
    usuario = get_user_model()(username="jefa", rol=ENCARGADO)

    assert usuario.puede("resultados.validar") is True
    assert usuario.puede("pagos.anular") is False
