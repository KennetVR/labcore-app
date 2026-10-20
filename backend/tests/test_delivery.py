import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.base import ContentFile

from catalogo.models import Examen
from ordenes.models import Orden, OrdenItem
from reportes.models import Reporte


@pytest.fixture(autouse=True)
def correo(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture(autouse=True)
def media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def usuario_rol(rol, nombre="jefa"):
    return get_user_model().objects.create_user(
        username=nombre, password="qa-pass-2026", rol=rol
    )


def crear_orden_con_reporte(estado=Orden.Estado.PDF):
    orden = Orden.objects.create(estado=estado)
    examen = Examen.objects.create(codigo="GLU", nombre="Glucosa")
    OrdenItem.objects.create(orden=orden, examen=examen, resultado="95", bandera="")
    reporte = Reporte.objects.create(orden=orden, codigo_qr="LAB-R1")
    reporte.pdf.save("R1.pdf", ContentFile(b"%PDF-1.4 fake"), save=True)
    return orden, reporte


@pytest.mark.django_db
def test_entrega_sin_correo_marca_entregada(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, reporte = crear_orden_con_reporte()

    resp = api.post(f"/api/ordenes/{orden.id}/entrega/", {}, format="json")

    assert resp.status_code == 200
    orden.refresh_from_db()
    reporte.refresh_from_db()
    assert orden.estado == Orden.Estado.ENTREGADA
    assert reporte.entregado_at is not None
    assert reporte.entregado_por == api.handler._force_user
    assert reporte.enviado_a == ""
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_entrega_con_correo_envia_el_pdf(api):
    api.force_authenticate(user=usuario_rol("reportes"))
    orden, reporte = crear_orden_con_reporte()

    resp = api.post(
        f"/api/ordenes/{orden.id}/entrega/",
        {"enviado_a": "ana@example.com"},
        format="json",
    )

    assert resp.status_code == 200
    assert len(mail.outbox) == 1
    mensaje = mail.outbox[0]
    assert mensaje.to == ["ana@example.com"]
    assert mensaje.attachments[0][0] == f"{reporte.numero}.pdf"
    assert mensaje.attachments[0][2] == "application/pdf"
    orden.refresh_from_db()
    reporte.refresh_from_db()
    assert orden.estado == Orden.Estado.ENTREGADA
    assert reporte.enviado_a == "ana@example.com"


@pytest.mark.django_db
def test_no_entrega_sin_reporte(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden = Orden.objects.create(estado=Orden.Estado.VALIDADA)

    resp = api.post(f"/api/ordenes/{orden.id}/entrega/", {}, format="json")

    assert resp.status_code == 400
    assert "detail" in resp.data
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.VALIDADA


@pytest.mark.django_db
def test_auxiliar_no_entrega(api, usuario):
    api.force_authenticate(user=usuario)
    orden, reporte = crear_orden_con_reporte()

    resp = api.post(f"/api/ordenes/{orden.id}/entrega/", {}, format="json")

    assert resp.status_code == 403
    reporte.refresh_from_db()
    assert reporte.entregado_at is None


@pytest.mark.django_db
def test_no_entrega_dos_veces(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, _ = crear_orden_con_reporte(estado=Orden.Estado.ENTREGADA)

    resp = api.post(f"/api/ordenes/{orden.id}/entrega/", {}, format="json")

    assert resp.status_code == 400
    assert "detail" in resp.data


@pytest.mark.django_db
def test_correo_invalido_no_entrega(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, reporte = crear_orden_con_reporte()

    resp = api.post(
        f"/api/ordenes/{orden.id}/entrega/",
        {"enviado_a": "no-es-correo"},
        format="json",
    )

    assert resp.status_code == 400
    orden.refresh_from_db()
    reporte.refresh_from_db()
    assert orden.estado == Orden.Estado.PDF
    assert reporte.entregado_at is None
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_fallo_de_correo_no_marca_entrega(api, monkeypatch):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, reporte = crear_orden_con_reporte()

    def boom(*args, **kwargs):
        raise OSError("smtp caido")

    monkeypatch.setattr("api.views.enviar_reporte_por_correo", boom)
    resp = api.post(
        f"/api/ordenes/{orden.id}/entrega/",
        {"enviado_a": "ana@example.com"},
        format="json",
    )

    assert resp.status_code == 502
    orden.refresh_from_db()
    reporte.refresh_from_db()
    assert orden.estado == Orden.Estado.PDF
    assert reporte.entregado_at is None
    assert reporte.enviado_a == ""


@pytest.mark.django_db
def test_no_reentrega_tras_revertir_el_estado(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, reporte = crear_orden_con_reporte()
    api.post(
        f"/api/ordenes/{orden.id}/entrega/",
        {"enviado_a": "ana@example.com"},
        format="json",
    )

    revertir = api.patch(
        f"/api/ordenes/{orden.id}/", {"estado": Orden.Estado.PDF}, format="json"
    )
    assert revertir.status_code == 200
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.PDF
    resp = api.post(
        f"/api/ordenes/{orden.id}/entrega/",
        {"enviado_a": "otra@example.com"},
        format="json",
    )

    assert resp.status_code == 400
    assert "detail" in resp.data
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]


@pytest.mark.django_db
def test_cuerpo_invalido_no_entrega(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, reporte = crear_orden_con_reporte()

    resp = api.post(f"/api/ordenes/{orden.id}/entrega/", [], format="json")

    assert resp.status_code == 400
    orden.refresh_from_db()
    reporte.refresh_from_db()
    assert orden.estado == Orden.Estado.PDF
    assert reporte.entregado_at is None


@pytest.mark.django_db
def test_no_entrega_en_estado_anterior(api):
    api.force_authenticate(user=usuario_rol("encargada"))
    orden, reporte = crear_orden_con_reporte(estado=Orden.Estado.VALIDADA)

    resp = api.post(f"/api/ordenes/{orden.id}/entrega/", {}, format="json")

    assert resp.status_code == 400
    orden.refresh_from_db()
    reporte.refresh_from_db()
    assert orden.estado == Orden.Estado.VALIDADA
    assert reporte.entregado_at is None
