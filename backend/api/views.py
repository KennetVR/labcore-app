from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from catalogo.models import (
    Cliente,
    Examen,
    Paquete,
    TarifarioExamen,
    TarifarioPaquete,
    Zona,
)
from ordenes.models import Orden
from pacientes.models import Paciente

from .serializers import (
    ClienteSerializer,
    ExamenSerializer,
    OrdenSerializer,
    PaqueteSerializer,
    PacienteSerializer,
    TarifarioExamenSerializer,
    TarifarioPaqueteSerializer,
    ZonaSerializer,
)


class ProtectedDestroyMixin:
    """Convierte un borrado bloqueado por referencias en un 409 explicable."""

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "No se puede eliminar: el registro está en uso por otros datos."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )


class ZonaViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Zona.objects.all()
    serializer_class = ZonaSerializer


class ClienteViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    search_fields = ["nombre", "contacto"]


class ExamenViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Examen.objects.all()
    serializer_class = ExamenSerializer
    search_fields = ["codigo", "nombre"]


class PaqueteViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Paquete.objects.all()
    serializer_class = PaqueteSerializer
    search_fields = ["nombre"]


class PacienteViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    search_fields = ["dni", "apellidos", "nombres"]


class TarifarioExamenViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = TarifarioExamen.objects.select_related("examen", "zona", "cliente")
    serializer_class = TarifarioExamenSerializer
    search_fields = ["examen__codigo", "examen__nombre"]


class TarifarioPaqueteViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = TarifarioPaquete.objects.select_related("paquete", "zona", "cliente")
    serializer_class = TarifarioPaqueteSerializer
    search_fields = ["paquete__nombre"]


class OrdenViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Orden.objects.all()
    serializer_class = OrdenSerializer
    search_fields = ["numero", "paciente__dni", "paciente__apellidos"]

    @action(detail=False, methods=["post"])
    def cotizar(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.quotation)
