import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def usuario(db):
    """Persona operativa: el encargado del laboratorio."""
    return get_user_model().objects.create_user(
        username="qa", password="qa-pass-2026", rol="encargada"
    )


@pytest.fixture
def administrador(db):
    return get_user_model().objects.create_user(
        username="admin-qa", password="qa-pass-2026", rol="admin"
    )
