from urllib.parse import urlsplit

import pytest
from django.contrib.auth import get_user_model

from ordenes.models import Orden
from reportes.models import Reporte


@pytest.fixture
def issued_report(api, settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    settings.REPORT_VERIFICATION_BASE_URL = "https://lab.example"
    import reportes.pdf as pdf

    captured = []
    original = pdf.qrcode.make

    def capture(data):
        captured.append(data)
        return original(data)

    monkeypatch.setattr(pdf.qrcode, "make", capture)
    user = get_user_model().objects.create_user(username="issuer", rol="encargada")
    api.force_authenticate(user=user)
    order = Orden.objects.create(estado=Orden.Estado.VALIDADA)
    response = api.post(f"/api/ordenes/{order.pk}/reporte/", {}, format="json")
    assert response.status_code == 201
    report = Reporte.objects.get(orden=order)
    api.force_authenticate(user=None)
    assert captured[0].startswith("https://lab.example/verificar/")
    return report, urlsplit(captured[0]).path


@pytest.mark.django_db
def test_public_verification_only_displays_report_number(api, issued_report):
    report, path = issued_report
    before = list(Reporte.objects.values())
    response = api.get(path)
    assert response.status_code == 200
    text = response.content.decode()
    assert "Reporte registrado en LabCore" in text
    assert report.numero in text
    for private in ("issuer", "Paciente", "Resultado", "pdf/", "href=", "enviado_a"):
        assert private not in text
    assert "no-store" in response["Cache-Control"]
    assert response["Referrer-Policy"] == "no-referrer"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert list(Reporte.objects.values()) == before
    assert api.get(f"/api/reportes/{report.pk}/pdf/").status_code in (401, 403)


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["tampered", "number", "deleted", "no_pdf"])
def test_unverifiable_link_discloses_no_report(api, issued_report, kind):
    report, path = issued_report
    if kind == "tampered":
        path = path.rstrip("/") + "x/"
    elif kind == "number":
        path = f"/verificar/{report.numero}/"
    elif kind == "deleted":
        report.delete()
    else:
        report.pdf = ""
        report.save(update_fields=["pdf"])
    response = api.get(path)
    assert response.status_code == 404
    assert "No se pudo verificar el reporte" in response.content.decode()
    assert report.numero not in response.content.decode()


@pytest.mark.django_db
def test_verification_rejects_writes(api, issued_report):
    report, path = issued_report
    before = list(Reporte.objects.values())
    assert api.post(path, {}, format="json").status_code == 405
    assert list(Reporte.objects.values()) == before
