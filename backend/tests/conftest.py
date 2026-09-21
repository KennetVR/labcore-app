import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def usuario(db):
    return get_user_model().objects.create_user(username="qa", password="qa-pass-2026")