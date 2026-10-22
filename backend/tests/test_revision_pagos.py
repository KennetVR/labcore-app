"""Correcciones de la revision independiente: busqueda, bandera manual y motivo."""
import pytest
from django.contrib.auth import get_user_model

from catalogo.models import Cliente, Examen
from facturacion.models import Pago
from ordenes.models import Orden, OrdenItem
from tests.test_pagos import crear_orden_con_total, usuario_con_rol


# --- B1: la busqueda textual filtra de verdad ------------------------------


@pytest.mark.django_db
def test_la_busqueda_textual_filtra_pagos(api):
    cliente = Cliente.objects.create(nombre="Clinica Alfa")
    o1 = crear_orden_con_total(cliente=cliente)
    o2 = crear_orden_con_total()
    api.force_authenticate(user=usuario_con_rol("reportes"))
    api.post("/api/pagos/", {"orden": o1.id, "monto": "10", "forma_pago": "contado",
                             "observacion": "Anticipo unico"}, format="json")
    api.post("/api/pagos/", {"orden": o2.id, "monto": "20", "forma_pago": "contado",
                             "observacion": "otro"}, format="json")

    assert api.get("/api/pagos/?search=Anticipo").data["count"] == 1
    assert api.get(f"/api/pagos/?search={cliente.nombre}").data["count"] == 1
    assert api.get(f"/api/pagos/?search={o1.numero}").data["count"] == 1
    assert api.get("/api/pagos/?search=INEXISTENTE").data["count"] == 0


# --- B2: la bandera manual sobrevive a un guardado posterior ----------------


@pytest.mark.django_db
def test_la_bandera_manual_sobrevive_a_un_guardado_posterior(api, usuario):
    examen = Examen.objects.create(codigo="MAN", nombre="Manual", ref_min="70", ref_max="100")
    orden = Orden.objects.create()
    item = OrdenItem.objects.create(orden=orden, examen=examen)
    api.force_authenticate(user=usuario)
    api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "150", "bandera": "H*", "bandera_manual": True}]},
        format="json",
    )
    item.refresh_from_db()
    assert item.bandera == "H*"
    assert item.bandera_manual is True

    # Un cliente que no manda el flag no debe pisar la bandera manual.
    api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "150", "bandera": "H*"}]},
        format="json",
    )
    item.refresh_from_db()
    assert item.bandera == "H*"
    assert item.bandera_manual is True


@pytest.mark.django_db
def test_el_flag_booleano_no_confunde_la_cadena_false(api, usuario):
    examen = Examen.objects.create(codigo="STR", nombre="String", ref_min="70", ref_max="100")
    orden = Orden.objects.create()
    item = OrdenItem.objects.create(orden=orden, examen=examen)
    api.force_authenticate(user=usuario)

    api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": item.id, "resultado": "95", "bandera": "H", "bandera_manual": "false"}]},
        format="json",
    )

    item.refresh_from_db()
    assert item.bandera == ""
    assert item.bandera_manual is False


# --- B3: anular exige un motivo de verdad ----------------------------------


@pytest.mark.django_db
def test_anular_rechaza_motivo_nulo(api):
    orden = crear_orden_con_total()
    api.force_authenticate(user=usuario_con_rol("reportes"))
    creado = api.post("/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"},
                      format="json")

    resp = api.post(f"/api/pagos/{creado.data['id']}/anular/", {"motivo": None}, format="json")

    assert resp.status_code == 400
    assert Pago.objects.get(pk=creado.data["id"]).anulado is False


@pytest.mark.django_db
def test_anular_rechaza_motivo_no_texto(api):
    orden = crear_orden_con_total()
    api.force_authenticate(user=usuario_con_rol("reportes"))
    creado = api.post("/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"},
                      format="json")

    resp = api.post(f"/api/pagos/{creado.data['id']}/anular/", {"motivo": 42}, format="json")

    assert resp.status_code == 400
    assert Pago.objects.get(pk=creado.data["id"]).anulado is False


# --- A1: el listado de ordenes no multiplica las consultas -----------------


@pytest.mark.django_db
def test_el_listado_de_ordenes_expone_el_saldo_sin_consultar_por_orden(api, usuario):
    cliente = Cliente.objects.create(nombre="Clinica Query")
    orden = crear_orden_con_total(cliente=cliente)
    api.force_authenticate(user=usuario_con_rol("reportes"))
    api.post("/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"},
             format="json")

    with django_assert_num_queries_limite(40):
        resp = api.get("/api/ordenes/")

    assert resp.status_code == 200
    fila = next(o for o in resp.data["results"] if o["id"] == orden.id)
    assert fila["total_pagado"] == "50.00"
    assert fila["saldo"] == "150.00"


import contextlib

import django.db
from django.test.utils import CaptureQueriesContext


@contextlib.contextmanager
def django_assert_num_queries_limite(limite):
    with CaptureQueriesContext(django.db.connection) as capturas:
        yield capturas
    assert len(capturas) <= limite, f"{len(capturas)} consultas (limite {limite})"
