from rest_framework import viewsets

from catalogo.models import Cliente, Examen, Paquete, Zona
from ordenes.models import Orden
from pacientes.models import Paciente

from .serializers import (
    ClienteSerializer,
    ExamenSerializer,
    OrdenSerializer,
    PaqueteSerializer,
    PacienteSerializer,
    ZonaSerializer,
)


class ZonaViewSet(viewsets.ModelViewSet):
    queryset = Zona.objects.all()
    serializer_class = ZonaSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    search_fields = ["nombre", "contacto"]


class ExamenViewSet(viewsets.ModelViewSet):
    queryset = Examen.objects.all()
    serializer_class = ExamenSerializer
    search_fields = ["codigo", "nombre"]


class PaqueteViewSet(viewsets.ModelViewSet):
    queryset = Paquete.objects.all()
    serializer_class = PaqueteSerializer
    search_fields = ["nombre"]


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    search_fields = ["dni", "apellidos", "nombres"]


class OrdenViewSet(viewsets.ModelViewSet):
    queryset = Orden.objects.all()
    serializer_class = OrdenSerializer
    search_fields = ["numero", "paciente__dni", "paciente__apellidos"]