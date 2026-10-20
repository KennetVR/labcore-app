import pytest

from catalogo.models import Examen, Paquete, PaqueteExamen


@pytest.mark.django_db
def test_crea_paquete_con_examenes_en_orden(api, usuario):
    api.force_authenticate(user=usuario)
    glucosa = Examen.objects.create(codigo="GLU", nombre="Glucosa")
    hemograma = Examen.objects.create(codigo="HEM", nombre="Hemograma")

    resp = api.post(
        "/api/paquetes/",
        {
            "nombre": "Control Anual",
            "frecuencia": "semestral",
            "examenes": [
                {"examen": hemograma.id, "orden": 1},
                {"examen": glucosa.id, "orden": 0},
            ],
        },
        format="json",
    )

    assert resp.status_code == 201
    paquete = Paquete.objects.get(nombre="Control Anual")
    miembros = list(
        PaqueteExamen.objects.filter(paquete=paquete)
        .order_by("orden")
        .values_list("examen_id", "orden")
    )
    assert miembros == [(glucosa.id, 0), (hemograma.id, 1)]
    assert resp.data["examenes"] == [
        {"orden": 0, "examen": glucosa.id},
        {"orden": 1, "examen": hemograma.id},
    ]


@pytest.mark.django_db
def test_actualiza_miembros_del_paquete(api, usuario):
    api.force_authenticate(user=usuario)
    paquete = Paquete.objects.create(nombre="Control", frecuencia="mensual")
    glucosa = Examen.objects.create(codigo="GLU", nombre="Glucosa")
    hemograma = Examen.objects.create(codigo="HEM", nombre="Hemograma")
    PaqueteExamen.objects.create(paquete=paquete, examen=glucosa, orden=0)

    resp = api.patch(
        f"/api/paquetes/{paquete.id}/",
        {"examenes": [{"examen": hemograma.id, "orden": 0}]},
        format="json",
    )

    assert resp.status_code == 200
    assert list(paquete.examenes_compuestos.values_list("examen_id", flat=True)) == [
        hemograma.id
    ]


@pytest.mark.django_db
def test_rechaza_examenes_repetidos_o_inexistentes(api, usuario):
    api.force_authenticate(user=usuario)
    glucosa = Examen.objects.create(codigo="GLU", nombre="Glucosa")

    repetido = api.post(
        "/api/paquetes/",
        {
            "nombre": "Repetido",
            "frecuencia": "mensual",
            "examenes": [glucosa.id, glucosa.id],
        },
        format="json",
    )
    inexistente = api.post(
        "/api/paquetes/",
        {"nombre": "Fantasma", "frecuencia": "mensual", "examenes": [9999]},
        format="json",
    )

    assert repetido.status_code == 400
    assert "examenes" in repetido.data
    assert inexistente.status_code == 400
    assert "examenes" in inexistente.data
    assert Paquete.objects.count() == 0


@pytest.mark.django_db
def test_listado_conserva_la_forma_de_examenes(api, usuario):
    api.force_authenticate(user=usuario)
    paquete = Paquete.objects.create(nombre="Control", frecuencia="mensual")
    glucosa = Examen.objects.create(codigo="GLU", nombre="Glucosa")
    hemograma = Examen.objects.create(codigo="HEM", nombre="Hemograma")
    PaqueteExamen.objects.create(paquete=paquete, examen=glucosa, orden=0)
    PaqueteExamen.objects.create(paquete=paquete, examen=hemograma, orden=1)

    resp = api.get("/api/paquetes/")

    assert resp.status_code == 200
    row = next(r for r in resp.data["results"] if r["id"] == paquete.id)
    assert row["examenes"] == [
        {"orden": 0, "examen": glucosa.id},
        {"orden": 1, "examen": hemograma.id},
    ]
