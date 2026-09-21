import pytest

from catalogo.models import Examen, Paquete, TarifarioPaquete, Zona
from ordenes.models import Orden


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