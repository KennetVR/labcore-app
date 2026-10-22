from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.base import ContentFile

from ordenes.models import Orden
from reportes.models import Reporte


@pytest.fixture
def delivered(api, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    user = get_user_model().objects.create_user(username="sender", rol="encargada")
    api.force_authenticate(user=user)
    order = Orden.objects.create(estado="pdf")
    report = Reporte.objects.create(orden=order)
    report.pdf.save("result.pdf", ContentFile(b"%PDF-original"))
    assert api.post(f"/api/ordenes/{order.pk}/entrega/", {}, format="json").status_code == 200
    report.refresh_from_db()
    return order, report, user


def resend(api, order, **overrides):
    body = {"enviado_a": "other@example.com", "solicitud": str(uuid4()), **overrides}
    return api.post(f"/api/ordenes/{order.pk}/reenviar/", body, format="json")


@pytest.mark.django_db
def test_resend_new_recipient_preserves_first_delivery_and_pdf(api, delivered):
    order, report, user = delivered
    before = Reporte.objects.values().get(pk=report.pk)
    response = resend(api, order)
    assert response.status_code == 201
    assert mail.outbox[0].to == ["other@example.com"]
    assert mail.outbox[0].attachments[0][1] == b"%PDF-original"
    assert Reporte.objects.values().get(pk=report.pk) == before
    order.refresh_from_db()
    assert order.estado == "entregada"
    history = api.get(f"/api/ordenes/{order.pk}/envios/")
    assert history.status_code == 200
    event = history.data["results"][0]
    assert event["enviado_a"] == "other@example.com"
    assert event["estado"] == "enviado"
    assert event["usuario"] == user.username
    assert event["fecha"]


@pytest.mark.django_db
def test_repeat_request_does_not_send_twice(api, delivered):
    order, _, _ = delivered
    key = str(uuid4())
    assert resend(api, order, solicitud=key).status_code == 201
    assert resend(api, order, solicitud=key).status_code == 200
    assert resend(api, order, solicitud=key, enviado_a="changed@example.com").status_code == 409
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_failure_is_recorded_without_changing_first_delivery(api, delivered, monkeypatch):
    order, report, _ = delivered
    before = Reporte.objects.values().get(pk=report.pk)

    def fail(*args, **kwargs):
        raise OSError("private SMTP details")

    monkeypatch.setattr("api.views.enviar_reporte_por_correo", fail)
    key = str(uuid4())
    assert resend(api, order, solicitud=key).status_code == 502
    assert resend(api, order, solicitud=key).status_code == 409
    history = api.get(f"/api/ordenes/{order.pk}/envios/")
    assert history.data["count"] == 1
    assert history.data["results"][0]["estado"] == "fallido"
    assert "private SMTP" not in str(history.data)
    assert Reporte.objects.values().get(pk=report.pk) == before
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["auxiliar", "muestreo", None])
def test_history_and_resend_require_delivery_roles(api, delivered, role):
    order, _, user = delivered
    user.rol = role or "auxiliar"
    user.save()
    api.force_authenticate(user=user if role else None)
    assert resend(api, order).status_code == 403
    assert api.get(f"/api/ordenes/{order.pk}/envios/").status_code == 403
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("recipient", ["", "invalid", None, ["a@example.com"]])
def test_invalid_recipient_has_no_side_effects(api, delivered, recipient):
    order, _, _ = delivered
    assert resend(api, order, enviado_a=recipient).status_code == 400
    assert api.get(f"/api/ordenes/{order.pk}/envios/").data["count"] == 0
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_requires_first_delivery(api, delivered):
    order, report, _ = delivered
    report.entregado_at = None
    report.save(update_fields=["entregado_at"])
    assert resend(api, order).status_code == 400
    assert len(mail.outbox) == 0
