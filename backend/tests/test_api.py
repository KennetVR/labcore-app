import pytest

from catalogo.models import Examen, Paquete, TarifarioExamen, TarifarioPaquete, Zona
from ordenes.models import Orden, OrdenItem


@pytest.mark.django_db
def test_api_requiere_autenticacion(api):
    resp = api.get("/api/examenes/")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_crear_y_listar_zonas(api, usuario):
    api.force_authenticate(user=usuario)
    resp = api.post("/api/zonas/", {"nombre": "Lima"}, format="json")
    assert resp.status_code == 201
    assert Zona.objects.count() == 1
    resp = api.get("/api/zonas/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_crear_y_listar_examenes(api, usuario):
    api.force_authenticate(user=usuario)
    payload = {
        "codigo": "HB",
        "nombre": "Hemoglobina",
        "area": "sangre",
        "resultado_tipo": "numerico",
        "unidad": "g/dL",
    }
    resp = api.post("/api/examenes/", payload, format="json")
    assert resp.status_code == 201
    assert Examen.objects.count() == 1
    resp = api.get("/api/examenes/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_calculo_total_orden_con_paquete(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo="HB", nombre="Hemoglobina", area="sangre")
    paquete = Paquete.objects.create(nombre="Control Mensual", frecuencia="mensual")
    paquete.examenes_compuestos.create(examen=examen, orden=1)
    TarifarioPaquete.objects.create(paquete=paquete, precio="30.00")
    resp = api.post(
        "/api/ordenes/",
        {
            "estado": "registrada",
            "items": [
                {"paquete": paquete.id, "examen": examen.id, "cantidad": 1, "medicion": "unica"}
            ],
        },
        format="json",
    )
    assert resp.status_code == 201
    orden = Orden.objects.get(pk=resp.data["id"])
    assert orden.numero
    assert str(orden.calcular_total()) == "30.00"
    assert resp.data["total"] == "30.00"


@pytest.mark.django_db
def test_rechaza_orden_si_un_examen_no_tiene_tarifa(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo="FERR", nombre="Ferritina", area="sangre")

    resp = api.post(
        "/api/ordenes/",
        {
            "estado": "registrada",
            "items": [{"examen": examen.id, "cantidad": 1, "medicion": "unica"}],
        },
        format="json",
    )

    assert resp.status_code == 400
    assert "No hay una tarifa vigente para el examen FERR" in str(resp.data["items"][0])
    assert Orden.objects.count() == 0
    assert OrdenItem.objects.count() == 0


@pytest.mark.django_db
def test_total_es_null_para_orden_historica_sin_tarifa(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo="FERR", nombre="Ferritina", area="sangre")
    orden = Orden.objects.create()
    OrdenItem.objects.create(orden=orden, examen=examen)

    resp = api.get(f"/api/ordenes/{orden.id}/")

    assert resp.status_code == 200
    assert resp.data["total"] is None
    assert orden.calcular_total() is None


@pytest.mark.django_db
def test_rechaza_tarifa_zonal_si_la_orden_no_tiene_cliente(api, usuario):
    api.force_authenticate(user=usuario)
    zona = Zona.objects.create(nombre="Lima Norte")
    examen = Examen.objects.create(codigo="HB", nombre="Hemoglobina", area="sangre")
    TarifarioExamen.objects.create(examen=examen, zona=zona, precio="17.00")

    resp = api.post(
        "/api/ordenes/",
        {
            "estado": "registrada",
            "items": [{"examen": examen.id, "cantidad": 1, "medicion": "unica"}],
        },
        format="json",
    )

    assert resp.status_code == 400
    assert "No hay una tarifa vigente para el examen HB" in str(resp.data["items"][0])
    assert Orden.objects.count() == 0
    assert OrdenItem.objects.count() == 0
