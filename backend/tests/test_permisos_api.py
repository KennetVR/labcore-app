"""Matriz rol x acción x estado de la política de dos roles.

Complementa ``test_permisos.py`` (capacidades) con las consecuencias observables
en la API: quién puede qué, sobre qué estado y sin efectos cuando se deniega.
"""

import pytest
from django.contrib import admin as django_admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

from accounts.admin import UsuarioAdmin
from accounts.models import Usuario
from catalogo.models import (
    Cliente,
    Examen,
    Paquete,
    TarifarioExamen,
    TarifarioPaquete,
    Zona,
)
from core.admin import BitacoraAdmin
from core.models import Bitacora
from facturacion.models import Pago
from ordenes.models import Orden, OrdenItem
from pacientes.models import Paciente
from reportes.models import Reporte
from tests.test_pagos import crear_orden_con_total


def crear_examen(codigo="GLU"):
    return Examen.objects.create(codigo=codigo, nombre=f"Examen {codigo}")


def crear_paciente():
    return Paciente.objects.create(apellidos="Perez", nombres="Ana")


# --- S2/S3 catálogo y configuración ---------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ruta",
    [
        "/api/zonas/",
        "/api/examenes/",
        "/api/paquetes/",
        "/api/tarifario-examenes/",
        "/api/tarifario-paquetes/",
    ],
)
def test_el_encargado_lee_la_configuracion(api, usuario, ruta):
    api.force_authenticate(user=usuario)

    assert api.get(ruta).status_code == 200


@pytest.mark.django_db
def test_el_encargado_no_crea_configuracion(api, usuario):
    examen = crear_examen()
    paquete = Paquete.objects.create(nombre="Control", frecuencia="mensual")
    api.force_authenticate(user=usuario)

    respuestas = [
        api.post("/api/zonas/", {"nombre": "Lima"}, format="json"),
        api.post(
            "/api/examenes/", {"codigo": "HB", "nombre": "Hemoglobina"}, format="json"
        ),
        api.post(
            "/api/paquetes/", {"nombre": "Nuevo", "frecuencia": "mensual"}, format="json"
        ),
        api.post(
            "/api/tarifario-examenes/",
            {"examen": examen.id, "precio": "10.00"},
            format="json",
        ),
        api.post(
            "/api/tarifario-paquetes/",
            {"paquete": paquete.id, "precio": "20.00"},
            format="json",
        ),
    ]

    assert [respuesta.status_code for respuesta in respuestas] == [403] * 5
    assert Zona.objects.count() == 0
    assert Examen.objects.count() == 1
    assert Paquete.objects.count() == 1
    assert TarifarioExamen.objects.count() == 0
    assert TarifarioPaquete.objects.count() == 0


@pytest.mark.django_db
def test_el_encargado_no_edita_ni_elimina_configuracion(api, usuario):
    examen = crear_examen()
    api.force_authenticate(user=usuario)

    editar = api.patch(
        f"/api/examenes/{examen.id}/", {"nombre": "Otro"}, format="json"
    )
    eliminar = api.delete(f"/api/examenes/{examen.id}/")

    assert editar.status_code == 403
    assert eliminar.status_code == 403
    examen.refresh_from_db()
    assert examen.nombre == "Examen GLU"


@pytest.mark.django_db
def test_el_administrador_configura(api, administrador):
    api.force_authenticate(user=administrador)

    examen = api.post(
        "/api/examenes/", {"codigo": "HB", "nombre": "Hemoglobina"}, format="json"
    )
    paquete = api.post(
        "/api/paquetes/", {"nombre": "Nuevo", "frecuencia": "mensual"}, format="json"
    )
    tarifa = api.post(
        "/api/tarifario-examenes/",
        {"examen": examen.data["id"], "precio": "10.00"},
        format="json",
    )

    assert examen.status_code == 201
    assert paquete.status_code == 201
    assert tarifa.status_code == 201


# --- S2/S3 pacientes y clientes -------------------------------------------


@pytest.mark.django_db
def test_el_encargado_registra_pacientes_y_clientes(api, usuario):
    api.force_authenticate(user=usuario)

    paciente = api.post(
        "/api/pacientes/", {"apellidos": "Perez", "nombres": "Ana"}, format="json"
    )
    cliente = api.post("/api/clientes/", {"nombre": "Clinica Sur"}, format="json")
    editar = api.patch(
        f"/api/pacientes/{paciente.data['id']}/",
        {"observaciones": "Sin alergias"},
        format="json",
    )

    assert paciente.status_code == 201
    assert cliente.status_code == 201
    assert editar.status_code == 200


@pytest.mark.django_db
def test_el_encargado_no_elimina_pacientes_ni_clientes(api, usuario):
    paciente = crear_paciente()
    cliente = Cliente.objects.create(nombre="Clinica Sur")
    api.force_authenticate(user=usuario)

    assert api.delete(f"/api/pacientes/{paciente.id}/").status_code == 403
    assert api.delete(f"/api/clientes/{cliente.id}/").status_code == 403
    assert Paciente.objects.filter(id=paciente.id).exists()
    assert Cliente.objects.filter(id=cliente.id).exists()


@pytest.mark.django_db
def test_el_administrador_elimina_registros_libres(api, administrador):
    paciente = crear_paciente()
    cliente = Cliente.objects.create(nombre="Clinica Sur")
    api.force_authenticate(user=administrador)

    assert api.delete(f"/api/pacientes/{paciente.id}/").status_code == 204
    assert api.delete(f"/api/clientes/{cliente.id}/").status_code == 204


# --- S5/S6 órdenes: estados y datos clínicos -------------------------------


@pytest.mark.django_db
def test_el_encargado_crea_y_edita_ordenes_abiertas(api, usuario):
    orden = Orden.objects.create()
    api.force_authenticate(user=usuario)

    resp = api.patch(
        f"/api/ordenes/{orden.id}/", {"observacion": "Ayuno"}, format="json"
    )

    assert resp.status_code == 200
    orden.refresh_from_db()
    assert orden.observacion == "Ayuno"


@pytest.mark.django_db
def test_no_se_edita_una_orden_validada(api, usuario):
    orden = Orden.objects.create(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=usuario)

    resp = api.patch(
        f"/api/ordenes/{orden.id}/", {"observacion": "Cambio tardío"}, format="json"
    )

    assert resp.status_code == 400
    orden.refresh_from_db()
    assert orden.observacion == ""


@pytest.mark.django_db
def test_el_estado_no_se_escribe_por_la_api(api, usuario):
    orden = Orden.objects.create()
    api.force_authenticate(user=usuario)

    resp = api.patch(
        f"/api/ordenes/{orden.id}/", {"estado": Orden.Estado.VALIDADA}, format="json"
    )

    assert resp.status_code == 400
    assert "estado" in resp.data
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.REGISTRADA


@pytest.mark.django_db
def test_no_acepta_resultados_al_crear_la_orden(api, usuario):
    examen = crear_examen()
    api.force_authenticate(user=usuario)

    resp = api.post(
        "/api/ordenes/",
        {
            "items": [
                {
                    "examen": examen.id,
                    "resultado": "95",
                    "bandera": "H",
                    "bandera_manual": True,
                }
            ]
        },
        format="json",
    )

    assert resp.status_code == 400
    assert "items" in resp.data
    assert Orden.objects.count() == 0


@pytest.mark.django_db
def test_el_encargado_no_elimina_ordenes(api, usuario):
    orden = Orden.objects.create()
    api.force_authenticate(user=usuario)

    assert api.delete(f"/api/ordenes/{orden.id}/").status_code == 403
    assert Orden.objects.filter(id=orden.id).exists()


@pytest.mark.django_db
def test_el_administrador_elimina_una_orden_sin_actividad(api, administrador):
    orden = Orden.objects.create()
    api.force_authenticate(user=administrador)

    assert api.delete(f"/api/ordenes/{orden.id}/").status_code == 204


@pytest.mark.django_db
def test_no_se_elimina_una_orden_con_pagos(api, administrador):
    orden = crear_orden_con_total()
    Pago.objects.create(orden=orden, monto="10.00", forma_pago="contado")
    api.force_authenticate(user=administrador)

    resp = api.delete(f"/api/ordenes/{orden.id}/")

    assert resp.status_code == 400
    assert Orden.objects.filter(id=orden.id).exists()


@pytest.mark.django_db
def test_no_se_elimina_una_orden_validada(api, administrador):
    orden = Orden.objects.create(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=administrador)

    resp = api.delete(f"/api/ordenes/{orden.id}/")

    assert resp.status_code == 400
    assert Orden.objects.filter(id=orden.id).exists()


# --- S6 reapertura auditada -----------------------------------------------


@pytest.mark.django_db
def test_solo_el_administrador_reabre(api, usuario):
    orden = Orden.objects.create(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=usuario)

    resp = api.post(
        f"/api/ordenes/{orden.id}/reabrir/", {"motivo": "Corregir"}, format="json"
    )

    assert resp.status_code == 403
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.VALIDADA


@pytest.mark.django_db
def test_reabrir_exige_motivo_y_estado_validada(api, administrador):
    orden = Orden.objects.create(estado=Orden.Estado.VALIDADA)
    api.force_authenticate(user=administrador)

    sin_motivo = api.post(f"/api/ordenes/{orden.id}/reabrir/", {}, format="json")

    orden.estado = Orden.Estado.PDF
    orden.save(update_fields=["estado"])
    con_reporte = api.post(
        f"/api/ordenes/{orden.id}/reabrir/", {"motivo": "Corregir"}, format="json"
    )

    assert sin_motivo.status_code == 400
    assert con_reporte.status_code == 400
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.PDF


@pytest.mark.django_db
def test_reabrir_deja_rastro_y_exige_nueva_validacion(api, administrador):
    orden = Orden.objects.create(estado=Orden.Estado.VALIDADA)
    examen = crear_examen()
    item = OrdenItem.objects.create(
        orden=orden,
        examen=examen,
        resultado="95",
        validado_por=administrador,
        validado_at=timezone.now(),
    )
    api.force_authenticate(user=administrador)

    resp = api.post(
        f"/api/ordenes/{orden.id}/reabrir/",
        {"motivo": "Corregir la unidad informada"},
        format="json",
    )

    assert resp.status_code == 200
    orden.refresh_from_db()
    item.refresh_from_db()
    assert orden.estado == Orden.Estado.RESULTADA
    assert item.validado_at is None
    assert item.validado_por is None
    bitacora = Bitacora.objects.get(usuario=administrador)
    assert orden.numero in bitacora.accion
    assert "Corregir la unidad informada" in bitacora.detalle

    revalidar = api.post(f"/api/ordenes/{orden.id}/validar/", {}, format="json")

    assert revalidar.status_code == 200
    orden.refresh_from_db()
    assert orden.estado == Orden.Estado.VALIDADA


# --- S7 pagos -------------------------------------------------------------


@pytest.mark.django_db
def test_el_encargado_cobra_pero_no_anula(api, usuario):
    orden = crear_orden_con_total()
    api.force_authenticate(user=usuario)

    creado = api.post(
        "/api/pagos/",
        {"orden": orden.id, "monto": "10", "forma_pago": "contado"},
        format="json",
    )
    anular = api.post(
        f"/api/pagos/{creado.data['id']}/anular/",
        {"motivo": "Error"},
        format="json",
    )

    assert creado.status_code == 201
    assert anular.status_code == 403
    pago = Pago.objects.get(pk=creado.data["id"])
    assert pago.anulado is False
    assert pago.motivo_anulacion == ""


# --- S4 un rol fuera de la política falla cerrado --------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metodo,ruta",
    [
        ("get", "/api/ordenes/"),
        ("get", "/api/pacientes/"),
        ("post", "/api/pacientes/"),
        ("get", "/api/pagos/"),
    ],
)
def test_un_rol_fuera_de_la_politica_no_accede(api, usuario, metodo, ruta):
    usuario.rol = "reportes"
    usuario.save()
    api.force_authenticate(user=usuario)

    resp = getattr(api, metodo)(ruta, {}, format="json")

    assert resp.status_code == 403


# --- S8 el admin de Django no es una vía alterna ---------------------------


@pytest.mark.django_db
def test_el_admin_de_django_solo_expone_identidades_y_bitacora():
    assert Usuario in django_admin.site._registry
    assert Bitacora in django_admin.site._registry

    for modelo in (Orden, OrdenItem, Reporte, Pago, Paciente, Cliente, Examen, Zona):
        assert modelo not in django_admin.site._registry


def _request(user):
    request = RequestFactory().get("/admin/")
    request.user = user
    return request


@pytest.mark.django_db
def test_el_admin_de_django_requiere_rol_administrador():
    root = get_user_model().objects.create_user(
        username="root",
        password="qa-pass-2026",
        rol="admin",
        is_staff=True,
        is_superuser=True,
    )
    encargada_staff = get_user_model().objects.create_user(
        username="encargada-staff",
        password="qa-pass-2026",
        rol="encargada",
        is_staff=True,
    )
    modelo_admin = UsuarioAdmin(Usuario, AdminSite())

    assert modelo_admin.has_module_permission(_request(root)) is True
    assert modelo_admin.has_module_permission(_request(encargada_staff)) is False


@pytest.mark.django_db
def test_la_bitacora_no_se_edita_en_el_admin():
    root = get_user_model().objects.create_user(
        username="root",
        password="qa-pass-2026",
        rol="admin",
        is_staff=True,
        is_superuser=True,
    )
    modelo_admin = BitacoraAdmin(Bitacora, AdminSite())
    request = _request(root)

    assert modelo_admin.has_add_permission(request) is False
    assert modelo_admin.has_change_permission(request) is False
    assert modelo_admin.has_delete_permission(request) is False
