from decimal import Decimal
from unittest.mock import patch

import pytest

from catalogo.models import Examen, Paquete, TarifarioExamen, TarifarioPaquete
from ordenes.models import Orden, OrdenItem


@pytest.mark.django_db
def test_quote_matches_saved_order_without_persisting(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo='HB', nombre='Hemoglobina')
    TarifarioExamen.objects.create(examen=examen, precio='12.50')
    paquete = Paquete.objects.create(nombre='Monthly', frecuencia='mensual')
    paquete.examenes_compuestos.create(examen=examen)
    TarifarioPaquete.objects.create(paquete=paquete, precio='30.00')
    payload = {'items': [
        {'examen': examen.pk, 'cantidad': 2},
        {'examen': examen.pk, 'paquete': paquete.pk, 'cantidad': 1},
    ]}
    response = api.post('/api/ordenes/cotizar/', payload, format='json')
    assert response.status_code == 200
    assert response.data == {
        'items': [
            {'precio_unitario': '12.50', 'subtotal': '25.00'},
            {'precio_unitario': '30.00', 'subtotal': '30.00'},
        ],
        'total': '55.00',
    }
    assert Orden.objects.count() == OrdenItem.objects.count() == 0
    saved = api.post('/api/ordenes/', payload, format='json')
    assert saved.status_code == 201
    assert saved.data['total'] == response.data['total']
    assert Orden.objects.count() == 1
    assert OrdenItem.objects.count() == 2


@pytest.mark.django_db
def test_missing_package_price_has_same_error_for_quote_and_save(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo='HB', nombre='Hemoglobina')
    TarifarioExamen.objects.create(examen=examen, precio=Decimal('0.00'))
    paquete = Paquete.objects.create(nombre='Missing', frecuencia='mensual')
    paquete.examenes_compuestos.create(examen=examen)
    payload = {'items': [
        {'examen': examen.pk},
        {'examen': examen.pk, 'paquete': paquete.pk},
    ]}
    quote = api.post('/api/ordenes/cotizar/', payload, format='json')
    saved = api.post('/api/ordenes/', payload, format='json')
    assert quote.status_code == saved.status_code == 400
    assert quote.data == saved.data
    assert len(quote.data['items']) == 2
    assert 'Missing' in str(quote.data['items'][1])
    assert Orden.objects.count() == OrdenItem.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('path', ['/api/ordenes/cotizar/', '/api/ordenes/'])
def test_package_rejects_unrelated_reference(api, usuario, path):
    api.force_authenticate(user=usuario)
    member = Examen.objects.create(codigo='MEMBER', nombre='Member')
    unrelated = Examen.objects.create(codigo='OTHER', nombre='Other')
    package = Paquete.objects.create(nombre='Package', frecuencia='mensual')
    package.examenes_compuestos.create(examen=member)
    TarifarioPaquete.objects.create(paquete=package, precio='23.40')
    response = api.post(path, {'items': [{'examen': unrelated.pk,
        'paquete': package.pk, 'cantidad': 2}]}, format='json')
    assert response.status_code == 400
    assert 'examen' in response.data['items'][0]
    assert Orden.objects.count() == OrdenItem.objects.count() == 0


@pytest.mark.django_db
def test_quote_requires_authentication(api):
    assert api.post('/api/ordenes/cotizar/', {'items': []}, format='json').status_code == 403


@pytest.mark.django_db
def test_order_creation_rolls_back_when_item_save_fails(api, usuario):
    api.force_authenticate(user=usuario)
    examen = Examen.objects.create(codigo='HB', nombre='Hemoglobina')
    TarifarioExamen.objects.create(examen=examen, precio='12.50')
    with patch('api.serializers.OrdenItem.objects.create', side_effect=RuntimeError('failure')):
        with pytest.raises(RuntimeError, match='failure'):
            api.post('/api/ordenes/', {'items': [{'examen': examen.pk}]}, format='json')
    assert Orden.objects.count() == OrdenItem.objects.count() == 0
