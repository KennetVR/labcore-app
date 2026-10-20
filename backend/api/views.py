from django.db import transaction
from django.db.models import ProtectedError
from django.utils import timezone
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

    @action(detail=True, methods=["post"])
    def resultados(self, request, pk=None):
        orden = self.get_object()
        if orden.estado in (
            Orden.Estado.VALIDADA,
            Orden.Estado.PDF,
            Orden.Estado.ENTREGADA,
        ):
            return Response(
                {"detail": "La orden ya está validada y no admite cambios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        entries = request.data.get("items")
        if not isinstance(entries, list):
            return Response(
                {"items": ["Se esperaba una lista de resultados."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        items = {item.id: item for item in orden.items.all()}
        cambios = []
        for entry in entries:
            item_id = entry.get("id") if isinstance(entry, dict) else None
            item = items.get(item_id)
            if item is None:
                return Response(
                    {"items": [f"El ítem {item_id} no pertenece a la orden."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            resultado = str(entry.get("resultado", "")).strip()
            bandera = str(entry.get("bandera", "")).strip()
            if len(resultado) > 100 or len(bandera) > 5:
                return Response(
                    {
                        "items": [
                            "El resultado o la bandera superan la longitud permitida."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cambios.append((item, resultado, bandera))

        with transaction.atomic():
            for item, resultado, bandera in cambios:
                item.resultado = resultado
                item.bandera = bandera
                item.save(update_fields=["resultado", "bandera"])
            self._actualizar_estado_resultados(orden)
        return Response(self.get_serializer(orden).data)

    def _actualizar_estado_resultados(self, orden):
        items = list(orden.items.all())
        if not items:
            return
        con_resultado = [item for item in items if item.resultado.strip()]
        if len(con_resultado) == len(items):
            orden.estado = Orden.Estado.RESULTADA
        elif con_resultado:
            orden.estado = Orden.Estado.EN_PROCESO
        orden.save(update_fields=["estado"])

    @action(detail=True, methods=["post"])
    def validar(self, request, pk=None):
        if getattr(request.user, "rol", "") not in ("admin", "encargada"):
            return Response(
                {"detail": "Solo la encargada o un administrador pueden validar."},
                status=status.HTTP_403_FORBIDDEN,
            )
        orden = self.get_object()
        if orden.estado in (Orden.Estado.PDF, Orden.Estado.ENTREGADA):
            return Response(
                {"detail": "La orden ya fue entregada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        items = list(orden.items.all())
        if not items or not all(item.resultado.strip() for item in items):
            return Response(
                {"detail": "Faltan resultados para validar la orden."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        validado_at = timezone.now()
        with transaction.atomic():
            orden.items.update(
                validado_por=request.user, validado_at=validado_at
            )
            orden.estado = Orden.Estado.VALIDADA
            orden.save(update_fields=["estado"])
        return Response(self.get_serializer(orden).data)
