"""Bandera automatica por rango de referencia del examen."""
from decimal import Decimal

import pytest

from catalogo.models import Examen
from ordenes.banderas import calcular_bandera, estado_rango, parsear_numero
from ordenes.models import Orden, OrdenItem


def crear_orden(codigo="GLU", **campos_examen):
    orden = Orden.objects.create()
    examen = Examen.objects.create(codigo=codigo, nombre="Glucosa", **campos_examen)
    item = OrdenItem.objects.create(orden=orden, examen=examen)
    return orden, item


# --- parseo del resultado -------------------------------------------------


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("95", Decimal("95")),
        ("95.5", Decimal("95.5")),
        (" 13,8 ", Decimal("13.8")),
        ("-2.5", Decimal("-2.5")),
        ("0", Decimal("0")),
    ],
)
def test_parsea_resultados_numericos(texto, esperado):
    assert parsear_numero(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    ["", "   ", "Negativo", "<0.5", ">200", "95 mg/dL", "1.234,5", "1,000", "NaN"],
)
def test_rechaza_resultados_no_numericos(texto):
    assert parsear_numero(texto) is None


# --- calculo de la bandera ------------------------------------------------


@pytest.mark.django_db
def test_sin_rango_no_calcula_bandera():
    _, item = crear_orden()
    assert calcular_bandera(item.examen, "150") == ""
    assert estado_rango(item.examen, "150") == "sin_rango"


@pytest.mark.django_db
def test_dentro_del_rango_es_normal():
    _, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))
    assert calcular_bandera(item.examen, "95") == ""
    assert estado_rango(item.examen, "95") == "normal"


@pytest.mark.django_db
def test_por_encima_del_rango_es_alto():
    _, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))
    assert calcular_bandera(item.examen, "150") == "H"
    assert estado_rango(item.examen, "150") == "alto"


@pytest.mark.django_db
def test_por_debajo_del_rango_es_bajo():
    _, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))
    assert calcular_bandera(item.examen, "45") == "L"
    assert estado_rango(item.examen, "45") == "bajo"


@pytest.mark.django_db
def test_los_extremos_del_rango_son_normales():
    _, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))
    assert calcular_bandera(item.examen, "70") == ""
    assert calcular_bandera(item.examen, "100") == ""


@pytest.mark.django_db
def test_solo_con_minimo_detecta_bajo():
    _, item = crear_orden(ref_min=Decimal("12"))
    assert calcular_bandera(item.examen, "11") == "L"
    assert calcular_bandera(item.examen, "15") == ""


@pytest.mark.django_db
def test_solo_con_maximo_detecta_alto():
    _, item = crear_orden(ref_max=Decimal("16"))
    assert calcular_bandera(item.examen, "17") == "H"
    assert calcular_bandera(item.examen, "15") == ""


@pytest.mark.django_db
def test_examen_de_texto_no_calcula():
    _, item = crear_orden(resultado_tipo="texto", ref_texto="Negativo")
    assert calcular_bandera(item.examen, "Negativo") == ""
    assert estado_rango(item.examen, "Negativo") == "sin_rango"


@pytest.mark.django_db
def test_resultado_no_numerico_no_calcula():
    _, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))
    assert calcular_bandera(item.examen, "No reactivo") == ""
    assert estado_rango(item.examen, "No reactivo") == "sin_rango"


# --- API: guardar resultados ---------------------------------------------


@pytest.mark.django_db
def test_guardar_resultados_calcula_la_bandera(api, usuario):
    api.force_authenticate(user=usuario)
    orden, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "150", "bandera": ""}]},
        format="json",
    )

    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bandera == "H"
    assert item.bandera_manual is False
    guardado = next(i for i in resp.data["items"] if i["id"] == item.id)
    assert guardado["bandera"] == "H"
    assert guardado["bandera_calculada"] == "H"
    assert guardado["rango_estado"] == "alto"
    assert guardado["ref_min"] == "70.0000"
    assert guardado["ref_max"] == "100.0000"


@pytest.mark.django_db
def test_guardar_resultados_dentro_de_rango_deja_la_bandera_vacia(api, usuario):
    api.force_authenticate(user=usuario)
    orden, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "95", "bandera": ""}]},
        format="json",
    )

    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bandera == ""
    guardado = next(i for i in resp.data["items"] if i["id"] == item.id)
    assert guardado["rango_estado"] == "normal"


@pytest.mark.django_db
def test_la_bandera_manual_del_laboratorio_tiene_prioridad(api, usuario):
    api.force_authenticate(user=usuario)
    orden, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {
            "items": [
                {
                    "id": item.id,
                    "resultado": "95",
                    "bandera": "H*",
                    "bandera_manual": True,
                }
            ]
        },
        format="json",
    )

    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bandera == "H*"
    assert item.bandera_manual is True
    guardado = next(i for i in resp.data["items"] if i["id"] == item.id)
    assert guardado["bandera"] == "H*"
    assert guardado["bandera_calculada"] == ""
    assert guardado["rango_estado"] == "normal"


@pytest.mark.django_db
def test_sin_rango_se_conserva_la_bandera_enviada(api, usuario):
    api.force_authenticate(user=usuario)
    orden, item = crear_orden()

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "95", "bandera": "H"}]},
        format="json",
    )

    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bandera == "H"
    guardado = next(i for i in resp.data["items"] if i["id"] == item.id)
    assert guardado["rango_estado"] == "sin_rango"


@pytest.mark.django_db
def test_recalcula_la_bandera_cuando_cambia_el_resultado(api, usuario):
    api.force_authenticate(user=usuario)
    orden, item = crear_orden(ref_min=Decimal("70"), ref_max=Decimal("100"))
    api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "150", "bandera": ""}]},
        format="json",
    )

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "95", "bandera": ""}]},
        format="json",
    )

    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bandera == ""
    assert item.bandera_manual is False
