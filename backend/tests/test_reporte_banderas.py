"""El reporte debe reflejar las banderas calculadas en el momento de generarse."""
import pytest
from django.contrib.auth import get_user_model

from catalogo.models import Examen
from ordenes.models import Orden, OrdenItem


def encargada():
    return get_user_model().objects.create_user(
        username="jefa-reporte", password="qa-pass-2026", rol="encargada"
    )


@pytest.mark.django_db
def test_el_reporte_calcula_la_bandera_de_los_items_sin_bandera(api):
    examen = Examen.objects.create(codigo="RP", nombre="Para reporte", ref_min="70", ref_max="100")
    orden = Orden.objects.create()
    OrdenItem.objects.create(orden=orden, examen=examen, resultado="150", bandera="")
    Orden.objects.filter(pk=orden.pk).update(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=encargada())

    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 201
    item = OrdenItem.objects.get(orden=orden)
    assert item.bandera == "H"


@pytest.mark.django_db
def test_el_reporte_no_pisa_una_bandera_manual(api):
    examen = Examen.objects.create(codigo="RQ", nombre="Manual", ref_min="70", ref_max="100")
    orden = Orden.objects.create()
    OrdenItem.objects.create(
        orden=orden, examen=examen, resultado="150", bandera="H*", bandera_manual=True
    )
    Orden.objects.filter(pk=orden.pk).update(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=encargada())

    resp = api.post(f"/api/ordenes/{orden.id}/reporte/", {}, format="json")

    assert resp.status_code == 201
    item = OrdenItem.objects.get(orden=orden)
    assert item.bandera == "H*"
    assert item.bandera_manual is True
