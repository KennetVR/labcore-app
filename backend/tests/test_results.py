import pytest
from django.contrib.auth import get_user_model

from catalogo.models import Examen
from ordenes.models import Orden, OrdenItem


def crear_orden(codigos=("GLU", "HEM")):
    orden = Orden.objects.create()
    glucosa = Examen.objects.create(codigo=codigos[0], nombre="Glucosa")
    hemograma = Examen.objects.create(codigo=codigos[1], nombre="Hemograma")
    primero = OrdenItem.objects.create(orden=orden, examen=glucosa)
    segundo = OrdenItem.objects.create(orden=orden, examen=hemograma)
    return orden, primero, segundo


@pytest.mark.django_db
def test_guarda_resultados_parciales(api, usuario):
    api.force_authenticate(user=usuario)
    orden, primero, _ = crear_orden()

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": primero.id, "resultado": "95", "bandera": ""}]},
        format="json",
    )

    assert resp.status_code == 200
    primero.refresh_from_db()
    orden.refresh_from_db()
    assert primero.resultado == "95"
    assert orden.estado == Orden.Estado.EN_PROCESO
    assert resp.data["estado"] == Orden.Estado.EN_PROCESO


@pytest.mark.django_db
def test_completar_resultados_pasa_a_resultada(api, usuario):
    api.force_authenticate(user=usuario)
    orden, primero, segundo = crear_orden()

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {
            "items": [
                {"id": primero.id, "resultado": "95", "bandera": ""},
                {"id": segundo.id, "resultado": "14.2", "bandera": "H"},
            ]
        },
        format="json",
    )

    assert resp.status_code == 200
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.RESULTADA


@pytest.mark.django_db
def test_no_valida_sin_todos_los_resultados(api, usuario):
    api.force_authenticate(user=usuario)
    orden, primero, _ = crear_orden()
    OrdenItem.objects.filter(id=primero.id).update(resultado="95")
    encargada = get_user_model().objects.create_user(
        username="jefa", password="qa-pass-2026", rol="encargada"
    )
    api.force_authenticate(user=encargada)

    resp = api.post(f"/api/ordenes/{orden.id}/validar/", {}, format="json")

    assert resp.status_code == 400
    assert "detail" in resp.data
    orden.refresh_from_db()
    assert orden.estado != Orden.Estado.VALIDADA


@pytest.mark.django_db
def test_valida_con_todos_los_resultados(api, usuario):
    orden, primero, segundo = crear_orden()
    encargada = get_user_model().objects.create_user(
        username="jefa", password="qa-pass-2026", rol="encargada"
    )
    api.force_authenticate(user=encargada)
    api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {
            "items": [
                {"id": primero.id, "resultado": "95", "bandera": ""},
                {"id": segundo.id, "resultado": "14.2", "bandera": "H"},
            ]
        },
        format="json",
    )

    resp = api.post(f"/api/ordenes/{orden.id}/validar/", {}, format="json")

    assert resp.status_code == 200
    orden.refresh_from_db()
    primero.refresh_from_db()
    assert orden.estado == Orden.Estado.VALIDADA
    assert primero.validado_por == encargada
    assert primero.validado_at is not None


@pytest.mark.django_db
def test_un_rol_fuera_de_la_politica_no_puede_validar(api, usuario):
    orden, primero, segundo = crear_orden()
    OrdenItem.objects.filter(orden=orden).update(resultado="1")
    usuario.rol = "auxiliar"
    usuario.save()
    api.force_authenticate(user=usuario)

    resp = api.post(f"/api/ordenes/{orden.id}/validar/", {}, format="json")

    assert resp.status_code == 403
    orden.refresh_from_db()
    assert orden.estado != Orden.Estado.VALIDADA


@pytest.mark.django_db
def test_orden_validada_no_admite_cambios(api, usuario):
    orden, primero, segundo = crear_orden()
    Orden.objects.filter(id=orden.id).update(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=usuario)

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": primero.id, "resultado": "10", "bandera": ""}]},
        format="json",
    )

    assert resp.status_code == 400
    primero.refresh_from_db()
    assert primero.resultado == ""


@pytest.mark.django_db
def test_no_acepta_items_de_otra_orden(api, usuario):
    orden, _, _ = crear_orden()
    otra, ajeno, _ = crear_orden(("GLU2", "HEM2"))
    api.force_authenticate(user=usuario)

    resp = api.post(
        f"/api/ordenes/{orden.id}/resultados/",
        {"items": [{"id": ajeno.id, "resultado": "10", "bandera": ""}]},
        format="json",
    )

    assert resp.status_code == 400
    ajeno.refresh_from_db()
    assert ajeno.resultado == ""
