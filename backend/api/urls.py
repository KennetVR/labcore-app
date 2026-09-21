from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClienteViewSet,
    ExamenViewSet,
    OrdenViewSet,
    PaqueteViewSet,
    PacienteViewSet,
    ZonaViewSet,
)

router = DefaultRouter()
router.register("zonas", ZonaViewSet)
router.register("clientes", ClienteViewSet)
router.register("examenes", ExamenViewSet)
router.register("paquetes", PaqueteViewSet)
router.register("pacientes", PacienteViewSet)
router.register("ordenes", OrdenViewSet)

urlpatterns = [
    path("", include(router.urls)),
]