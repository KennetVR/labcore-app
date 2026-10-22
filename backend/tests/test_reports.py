import pytest
from django.contrib.auth import get_user_model

from catalogo.models import Cliente, Examen
from ordenes.models import Orden, OrdenItem
from reportes.models import Reporte


@pytest.fixture(autouse=True)
def media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def crear_orden(estado=Orden.Estado.VALIDADA, cliente=None):
    orden = Orden.objects.create(estado=estado, cliente=cliente)
    glucosa = Examen.objects.create(codigo="GLU", nombre="Glucosa")
    OrdenItem.objects.create(orden=orden, examen=glucosa, resultado="95", bandera="")
    return orden


def encargada():
    return get_user_model().objects.create_user(
        username="jefa", password="qa-pass-2026", rol="encargada"
    )


@pytest.mark.django_db
def test_genera_reporte_de_orden_validada(api):
    usuario = encargada()
    api.force_authenticate(user=usuario)
    orden = crear_orden()

    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 201
    orden.refresh_from_db()
    reporte = Reporte.objects.get(orden=orden)
    assert orden.estado == Orden.Estado.PDF
    assert reporte.numero.startswith("R")
    assert reporte.generado_por == usuario
    assert reporte.pdf.name.endswith(".pdf")
    with reporte.pdf.open("rb") as archivo:
        assert archivo.read(4) == b"%PDF"
    assert resp.data["numero"] == reporte.numero


@pytest.mark.django_db
def test_no_genera_reporte_sin_validar(api):
    api.force_authenticate(user=encargada())
    orden = crear_orden(estado=Orden.Estado.RESULTADA)

    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 400
    assert Reporte.objects.count() == 0


@pytest.mark.django_db
def test_un_rol_fuera_de_la_politica_no_genera_reporte(api, usuario):
    usuario.rol = "auxiliar"
    usuario.save()
    api.force_authenticate(user=usuario)
    orden = crear_orden()

    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 403
    assert Reporte.objects.count() == 0


@pytest.mark.django_db
def test_segunda_generacion_es_idempotente(api):
    api.force_authenticate(user=encargada())
    orden = crear_orden()

    primero = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")
    segundo = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert primero.status_code == 201
    assert segundo.status_code == 200
    assert primero.data["numero"] == segundo.data["numero"]
    assert Reporte.objects.count() == 1


@pytest.mark.django_db
def test_descarga_el_pdf(api):
    api.force_authenticate(user=encargada())
    orden = crear_orden()
    api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")
    reporte = Reporte.objects.get(orden=orden)

    resp = api.get(f"/api/reportes/{reporte.id}/pdf/")

    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    cuerpo = b"".join(resp.streaming_content)
    assert cuerpo[:4] == b"%PDF"


@pytest.mark.django_db
def test_nombre_con_markup_no_rompe_el_reporte(api):
    api.force_authenticate(user=encargada())
    cliente = Cliente.objects.create(nombre="Clinica <Sur")
    orden = crear_orden(cliente=cliente)

    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 201
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.PDF


@pytest.mark.django_db
def test_fallo_de_generacion_no_deja_reporte(api, media, monkeypatch):
    api.force_authenticate(user=encargada())
    orden = crear_orden()

    def boom(self, story):
        raise OSError("disco lleno")

    monkeypatch.setattr("reportes.pdf.SimpleDocTemplate.build", boom)
    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 500
    assert Reporte.objects.count() == 0
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.VALIDADA
    assert not [p for p in media.rglob("*") if p.is_file()]
