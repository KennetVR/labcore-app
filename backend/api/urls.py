from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ClienteViewSet,
    ExamenViewSet,
    OrdenViewSet,
    PaqueteViewSet,
    PacienteViewSet,
    TarifarioExamenViewSet,
    TarifarioPaqueteViewSet,
    ZonaViewSet,
)

router = DefaultRouter()
router.register("zonas", ZonaViewSet)
router.register("clientes", ClienteViewSet)
router.register("examenes", ExamenViewSet)
router.register("paquetes", PaqueteViewSet)
router.register("pacientes", PacienteViewSet)
router.register("ordenes", OrdenViewSet)
router.register("tarifario-examenes", TarifarioExamenViewSet)
router.register("tarifario-paquetes", TarifarioPaqueteViewSet)

urlpatterns = [
    path("", include(router.urls)),
]