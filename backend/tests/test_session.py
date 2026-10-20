import pytest
from django.test import Client


@pytest.fixture
def browser():
    return Client(enforce_csrf_checks=True)


def csrf(browser):
    response = browser.get('/api/auth/session/')
    assert response.status_code == 200
    return response.json()['csrf_token']


@pytest.mark.django_db
def test_session_login_logout_with_real_csrf(browser, usuario):
    token = csrf(browser)
    old_cookie = browser.cookies['csrftoken'].value
    assert browser.get('/api/auth/session/').json()['user'] is None
    assert browser.get('/api/ordenes/').status_code == 403
    response = browser.post(
        '/api/auth/login/', {'username': 'qa', 'password': 'qa-pass-2026'},
        content_type='application/json', HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 200
    assert response.json()['user'] == {
        'id': usuario.pk, 'username': 'qa', 'name': 'qa', 'role': usuario.rol,
    }
    assert 'no-store' in response.headers['Cache-Control']
    assert browser.cookies['csrftoken'].value != old_cookie
    session_key = browser.cookies['sessionid'].value
    assert browser.post('/api/auth/logout/', HTTP_X_CSRFTOKEN=token).status_code == 403
    assert browser.get('/api/ordenes/').status_code == 200
    token = response.json()['csrf_token']
    assert browser.post('/api/auth/logout/').status_code == 403
    assert browser.get('/api/auth/session/').json()['user']['id'] == usuario.pk
    response = browser.post('/api/auth/logout/', HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 200
    assert response.json()['user'] is None
    assert browser.get('/api/ordenes/').status_code == 403
    browser.cookies['sessionid'] = session_key
    assert browser.get('/api/ordenes/').status_code == 403
    usuario.refresh_from_db()
    assert not usuario.is_staff and not usuario.is_superuser


@pytest.mark.django_db
def test_login_rejects_missing_csrf_and_foreign_origin(browser, usuario):
    payload = {'username': 'qa', 'password': 'qa-pass-2026'}
    assert browser.post('/api/auth/login/', payload).status_code == 403
    token = csrf(browser)
    response = browser.post(
        '/api/auth/login/', payload, content_type='application/json',
        HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='https://untrusted.example',
    )
    assert response.status_code == 403
    assert browser.get('/api/auth/session/').json()['user'] is None


@pytest.mark.django_db
@pytest.mark.parametrize('inactive', [False, True])
def test_login_invalid_credentials_do_not_create_session(browser, usuario, inactive):
    if inactive:
        usuario.is_active = False
        usuario.save()
    response = browser.post(
        '/api/auth/login/',
        {'username': 'qa', 'password': 'qa-pass-2026' if inactive else 'wrong'},
        content_type='application/json', HTTP_X_CSRFTOKEN=csrf(browser),
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'Invalid username or password.'}
    assert browser.get('/api/auth/session/').json()['user'] is None


@pytest.mark.django_db
@pytest.mark.parametrize('payload', ['{', '[]', '{"username": [], "password": 123}'])
def test_login_malformed_payload_is_rejected(browser, payload):
    response = browser.post(
        '/api/auth/login/', payload, content_type='application/json',
        HTTP_X_CSRFTOKEN=csrf(browser),
    )
    assert response.status_code == 400
    assert browser.get('/api/auth/session/').json()['user'] is None


@pytest.mark.django_db
def test_auth_get_requests_cannot_change_session(browser):
    assert browser.get('/api/auth/login/').status_code == 405
    assert browser.get('/api/auth/logout/').status_code == 405


@pytest.mark.django_db
def test_existing_collections_keep_session_contract(browser, usuario):
    for resource in ('zonas', 'clientes', 'examenes', 'paquetes', 'pacientes', 'ordenes'):
        assert browser.get(f'/api/{resource}/').status_code == 403
    browser.force_login(usuario)
    for resource in ('zonas', 'clientes', 'examenes', 'paquetes', 'pacientes', 'ordenes'):
        response = browser.get(f'/api/{resource}/')
        assert response.status_code == 200
        assert response.json() == {'count': 0, 'next': None, 'previous': None, 'results': []}
    assert browser.post('/api/ordenes/', {}, content_type='application/json').status_code == 403
