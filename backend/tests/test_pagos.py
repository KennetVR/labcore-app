"""Pagos, saldo pendiente, anulacion y estado de cuenta."""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from catalogo.models import Cliente, Examen, TarifarioExamen
from facturacion.models import Pago
from ordenes.models import Orden, OrdenItem


def crear_orden_con_total(cliente=None, precio="100.00", cantidad=2):
    orden = Orden.objects.create(cliente=cliente)
    examen = Examen.objects.create(codigo=f"EX{orden.id}", nombre="Examen de prueba")
    TarifarioExamen.objects.create(examen=examen, precio=Decimal(precio), activo=True)
    OrdenItem.objects.create(orden=orden, examen=examen, cantidad=cantidad)
    return orden


def crear_orden_sin_total():
    orden = Orden.objects.create()
    examen = Examen.objects.create(codigo=f"SIN{orden.id}", nombre="Sin tarifa")
    OrdenItem.objects.create(orden=orden, examen=examen)
    return orden


def usuario_con_rol(rol):
    return get_user_model().objects.create_user(
        username=f"u_{rol}", password="qa-pass-2026", rol=rol
    )


@pytest.fixture
def cobrador(db):
    """Encargado: registra pagos; la anulación queda reservada al administrador."""
    return get_user_model().objects.create_user(
        username="cobrador", password="qa-pass-2026", rol="encargada"
    )


# --- S1 registrar pagos ---------------------------------------------------


@pytest.mark.django_db
def test_registra_un_pago_de_la_orden(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)

    resp = api.post(
        "/api/pagos/",
        {"orden": orden.id, "monto": "50.00", "forma_pago": "contado", "observacion": "Abono"},
        format="json",
    )

    assert resp.status_code == 201
    assert resp.data["orden"] == orden.id
    assert resp.data["orden_numero"] == orden.numero
    assert resp.data["monto"] == "50.00"
    assert resp.data["forma_pago"] == "contado"
    assert resp.data["observacion"] == "Abono"
    assert resp.data["anulado"] is False
    assert resp.data["registrado_por_nombre"] == cobrador.username
    assert Pago.objects.filter(orden=orden).count() == 1


@pytest.mark.django_db
def test_rechaza_monto_cero_o_negativo(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "0", "forma_pago": "contado"}, format="json"
    )
    assert resp.status_code == 400

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "-10", "forma_pago": "contado"}, format="json"
    )
    assert resp.status_code == 400
    assert Pago.objects.count() == 0


@pytest.mark.django_db
def test_rechaza_pago_de_orden_sin_total(api, cobrador):
    orden = crear_orden_sin_total()
    api.force_authenticate(user=cobrador)

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "10", "forma_pago": "contado"}, format="json"
    )

    assert resp.status_code == 400
    assert Pago.objects.count() == 0


@pytest.mark.django_db
def test_rechaza_pago_que_supera_el_saldo(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "500", "forma_pago": "contado"}, format="json"
    )

    assert resp.status_code == 400
    assert Pago.objects.count() == 0


@pytest.mark.django_db
def test_admite_pagos_parciales_hasta_cubrir_el_total(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "120", "forma_pago": "contado"}, format="json"
    )
    assert resp.status_code == 201

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "80", "forma_pago": "boleta"}, format="json"
    )
    assert resp.status_code == 201

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "1", "forma_pago": "contado"}, format="json"
    )
    assert resp.status_code == 400


# --- S2 saldo pendiente ---------------------------------------------------


@pytest.mark.django_db
def test_el_detalle_de_la_orden_muestra_el_saldo(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "120", "forma_pago": "contado"}, format="json"
    )

    resp = api.get(f"/api/ordenes/{orden.id}/")

    assert resp.status_code == 200
    assert resp.data["total"] == "200.00"
    assert resp.data["total_pagado"] == "120.00"
    assert resp.data["saldo"] == "80.00"
    assert len(resp.data["pagos"]) == 1


@pytest.mark.django_db
def test_saldo_es_null_sin_total_y_cero_cuando_esta_cubierta(api, cobrador):
    sin_total = crear_orden_sin_total()
    cubierta = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    api.post(
        "/api/pagos/", {"orden": cubierta.id, "monto": "200", "forma_pago": "contado"}, format="json"
    )

    resp = api.get(f"/api/ordenes/{sin_total.id}/")
    assert resp.data["saldo"] is None
    assert resp.data["total_pagado"] == "0.00"

    resp = api.get(f"/api/ordenes/{cubierta.id}/")
    assert resp.data["saldo"] == "0.00"


# --- S3 inmutabilidad y anulacion -----------------------------------------


@pytest.mark.django_db
def test_un_pago_no_se_puede_editar_ni_borrar(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    creado = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"}, format="json"
    )
    pago_id = creado.data["id"]

    assert api.patch(f"/api/pagos/{pago_id}/", {"monto": "1"}, format="json").status_code == 405
    assert api.put(f"/api/pagos/{pago_id}/", {"monto": "1"}, format="json").status_code == 405
    assert api.delete(f"/api/pagos/{pago_id}/").status_code == 405
    assert Pago.objects.count() == 1


@pytest.mark.django_db
def test_anula_un_pago_con_motivo(api, cobrador, administrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    creado = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"}, format="json"
    )
    pago_id = creado.data["id"]

    api.force_authenticate(user=administrador)
    resp = api.post(
        f"/api/pagos/{pago_id}/anular/", {"motivo": "Monto mal tipeado"}, format="json"
    )

    assert resp.status_code == 200
    assert resp.data["anulado"] is True
    assert resp.data["motivo_anulacion"] == "Monto mal tipeado"
    assert resp.data["anulado_por_nombre"] == administrador.username
    assert resp.data["anulado_at"] is not None
    pago = Pago.objects.get(pk=pago_id)
    assert pago.anulado is True


@pytest.mark.django_db
def test_anular_exige_motivo(api, cobrador, administrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    creado = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"}, format="json"
    )

    api.force_authenticate(user=administrador)
    resp = api.post(f"/api/pagos/{creado.data['id']}/anular/", {}, format="json")

    assert resp.status_code == 400
    assert Pago.objects.get(pk=creado.data["id"]).anulado is False


@pytest.mark.django_db
def test_no_se_anula_dos_veces(api, cobrador, administrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    creado = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"}, format="json"
    )
    api.force_authenticate(user=administrador)
    api.post(
        f"/api/pagos/{creado.data['id']}/anular/", {"motivo": "Error"}, format="json"
    )

    resp = api.post(
        f"/api/pagos/{creado.data['id']}/anular/", {"motivo": "Otra vez"}, format="json"
    )

    assert resp.status_code == 400


@pytest.mark.django_db
def test_un_pago_anulado_no_cuenta_para_el_saldo(api, cobrador, administrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    creado = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "50", "forma_pago": "contado"}, format="json"
    )
    api.force_authenticate(user=administrador)
    api.post(f"/api/pagos/{creado.data['id']}/anular/", {"motivo": "Error"}, format="json")

    resp = api.get(f"/api/ordenes/{orden.id}/")

    assert resp.data["total_pagado"] == "0.00"
    assert resp.data["saldo"] == "200.00"
    assert len(resp.data["pagos"]) == 1
    assert resp.data["pagos"][0]["anulado"] is True


# --- S4 estado de cuenta --------------------------------------------------


@pytest.mark.django_db
def test_estado_de_cuenta_por_cliente(api, cobrador):
    cliente = Cliente.objects.create(nombre="Clínica San Juan")
    orden = crear_orden_con_total(cliente=cliente, precio="100.00", cantidad=2)
    api.force_authenticate(user=cobrador)
    api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "120", "forma_pago": "contado"}, format="json"
    )

    resp = api.get("/api/pagos/estado-cuenta/")

    assert resp.status_code == 200
    fila = next(f for f in resp.data if f["cliente"] == "Clínica San Juan")
    assert fila["facturado"] == "200.00"
    assert fila["pagado"] == "120.00"
    assert fila["saldo"] == "80.00"


@pytest.mark.django_db
def test_estado_de_cuenta_agrupa_particulares(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)

    resp = api.get("/api/pagos/estado-cuenta/")

    fila = next(f for f in resp.data if f["cliente"] == "Particular")
    assert fila["facturado"] == "200.00"
    assert fila["pagado"] == "0.00"


# --- S5 permisos ----------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["admin", "encargada"])
def test_los_roles_autorizados_registran_pagos(api, rol):
    orden = crear_orden_con_total()
    api.force_authenticate(user=usuario_con_rol(rol))

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "10", "forma_pago": "contado"}, format="json"
    )

    assert resp.status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize("rol", ["auxiliar", "muestreo"])
def test_los_roles_no_autorizados_no_registran_pagos(api, rol):
    orden = crear_orden_con_total()
    api.force_authenticate(user=usuario_con_rol(rol))

    resp = api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "10", "forma_pago": "contado"}, format="json"
    )

    assert resp.status_code == 403
    assert Pago.objects.count() == 0


@pytest.mark.django_db
def test_sin_sesion_no_se_consultan_ni_registran_pagos(api):
    orden = crear_orden_con_total()

    assert api.get("/api/pagos/").status_code == 403
    assert api.post(
        "/api/pagos/", {"orden": orden.id, "monto": "10", "forma_pago": "contado"}, format="json"
    ).status_code == 403


# --- S6 consulta ----------------------------------------------------------


@pytest.mark.django_db
def test_filtra_pagos_por_cliente_forma_y_anulado(api, cobrador, administrador):
    cliente = Cliente.objects.create(nombre="Clínica Norte")
    orden_a = crear_orden_con_total(cliente=cliente)
    orden_b = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    a = api.post(
        "/api/pagos/", {"orden": orden_a.id, "monto": "10", "forma_pago": "factura"}, format="json"
    )
    api.post(
        "/api/pagos/", {"orden": orden_b.id, "monto": "20", "forma_pago": "contado"}, format="json"
    )

    resp = api.get("/api/pagos/?cliente=" + str(cliente.id))
    assert resp.status_code == 200
    assert [p["id"] for p in resp.data["results"]] == [a.data["id"]]

    resp = api.get("/api/pagos/?forma_pago=contado")
    assert len(resp.data["results"]) == 1
    assert resp.data["results"][0]["forma_pago"] == "contado"

    api.force_authenticate(user=administrador)
    api.post(f"/api/pagos/{a.data['id']}/anular/", {"motivo": "Error"}, format="json")
    resp = api.get("/api/pagos/?anulado=true")
    assert len(resp.data["results"]) == 1
    resp = api.get("/api/pagos/?anulado=false")
    assert len(resp.data["results"]) == 1


@pytest.mark.django_db
def test_busqueda_por_numero_de_orden_y_observacion(api, cobrador):
    orden = crear_orden_con_total()
    api.force_authenticate(user=cobrador)
    api.post(
        "/api/pagos/",
        {"orden": orden.id, "monto": "10", "forma_pago": "contado", "observacion": "Anticipo"},
        format="json",
    )

    resp = api.get(f"/api/pagos/?search={orden.numero}")
    assert len(resp.data["results"]) == 1

    resp = api.get("/api/pagos/?search=Anticipo")
    assert len(resp.data["results"]) == 1
