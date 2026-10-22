import pytest

from catalogo.models import Cliente, Examen, TarifarioExamen, Zona
from ordenes.models import Orden, OrdenItem
from pacientes.models import Paciente


@pytest.mark.django_db
def test_no_elimina_paciente_con_ordenes(api, administrador):
    api.force_authenticate(user=administrador)
    paciente = Paciente.objects.create(apellidos="Perez", nombres="Ana")
    Orden.objects.create(paciente=paciente)

    resp = api.delete(f"/api/pacientes/{paciente.id}/")

    assert resp.status_code == 409
    assert "detail" in resp.data
    assert Paciente.objects.filter(id=paciente.id).exists()


@pytest.mark.django_db
def test_no_elimina_cliente_con_ordenes(api, administrador):
    api.force_authenticate(user=administrador)
    cliente = Cliente.objects.create(nombre="Clinica Sur")
    Orden.objects.create(cliente=cliente)

    resp = api.delete(f"/api/clientes/{cliente.id}/")

    assert resp.status_code == 409
    assert Cliente.objects.filter(id=cliente.id).exists()


@pytest.mark.django_db
def test_no_elimina_zona_con_clientes(api, administrador):
    api.force_authenticate(user=administrador)
    zona = Zona.objects.create(nombre="Lima Norte")
    Cliente.objects.create(nombre="Clinica Sur", zona=zona)

    resp = api.delete(f"/api/zonas/{zona.id}/")

    assert resp.status_code == 409
    assert Zona.objects.filter(id=zona.id).exists()


@pytest.mark.django_db
def test_no_elimina_examen_usado_en_ordenes(api, administrador):
    api.force_authenticate(user=administrador)
    examen = Examen.objects.create(codigo="GLU", nombre="Glucosa")
    orden = Orden.objects.create()
    OrdenItem.objects.create(orden=orden, examen=examen)

    resp = api.delete(f"/api/examenes/{examen.id}/")

    assert resp.status_code == 409
    assert Examen.objects.filter(id=examen.id).exists()


@pytest.mark.django_db
def test_elimina_registros_libres(api, administrador):
    api.force_authenticate(user=administrador)
    examen = Examen.objects.create(codigo="LIB", nombre="Libre")
    tarifa = TarifarioExamen.objects.create(examen=examen, precio="10.00")

    assert api.delete(f"/api/tarifario-examenes/{tarifa.id}/").status_code == 204
    assert api.delete(f"/api/examenes/{examen.id}/").status_code == 204
    assert Examen.objects.filter(id=examen.id).exists() is False
