import pytest

from catalogo.models import (
    Cliente,
    Examen,
    Paquete,
    TarifarioExamen,
    TarifarioPaquete,
    Zona,
)


@pytest.mark.django_db
def test_lista_y_crea_tarifa_de_examen(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo="HB", nombre="Hemoglobina")
    zona = Zona.objects.create(nombre="Lima Norte")
    cliente = Cliente.objects.create(nombre="Clinica Sur")
    tarifa = TarifarioExamen.objects.create(
        examen=examen, precio="12.50", zona=zona, cliente=cliente
    )

    resp = api.get("/api/tarifario-examenes/")

    assert resp.status_code == 200
    row = next(r for r in resp.data["results"] if r["id"] == tarifa.id)
    assert row["examen_codigo"] == "HB"
    assert row["examen_nombre"] == "Hemoglobina"
    assert row["zona_nombre"] == "Lima Norte"
    assert row["cliente_nombre"] == "Clinica Sur"
    assert row["precio"] == "12.50"

    created = api.post(
        "/api/tarifario-examenes/",
        {"examen": examen.id, "precio": "13.00"},
        format="json",
    )

    assert created.status_code == 201
    assert TarifarioExamen.objects.filter(precio="13.00").count() == 1


@pytest.mark.django_db
def test_lista_y_crea_tarifa_de_paquete(api, usuario):
    api.force_authenticate(user=usuario)
    paquete = Paquete.objects.create(nombre="Control Mensual", frecuencia="mensual")
    tarifa = TarifarioPaquete.objects.create(paquete=paquete, precio="45.00")

    resp = api.get("/api/tarifario-paquetes/")

    assert resp.status_code == 200
    row = next(r for r in resp.data["results"] if r["id"] == tarifa.id)
    assert row["paquete_nombre"] == "Control Mensual"
    assert row["precio"] == "45.00"

    created = api.post(
        "/api/tarifario-paquetes/",
        {"paquete": paquete.id, "precio": "47.00"},
        format="json",
    )

    assert created.status_code == 201
    assert TarifarioPaquete.objects.filter(precio="47.00").count() == 1
