from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import ProtectedError
from django.http import FileResponse
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
from reportes.correo import enviar_reporte_por_correo
from reportes.models import EnvioReporte, Reporte
from reportes.pdf import generar_pdf

from .serializers import (
    EnvioReporteSerializer,
    ReenvioSerializer,
    ClienteSerializer,
    ExamenSerializer,
    OrdenSerializer,
    PaqueteSerializer,
    PacienteSerializer,
    ReporteSerializer,
    TarifarioExamenSerializer,
    TarifarioPaqueteSerializer,
    ZonaSerializer,
)


def enviar_con_historial(orden, reporte, evento):
    try:
        enviar_reporte_por_correo(orden, reporte, evento.enviado_a)
    except Exception:
        evento.estado = EnvioReporte.Estado.FALLIDO
        evento.save(update_fields=["estado"])
        return False
    evento.estado = EnvioReporte.Estado.ENVIADO
    evento.save(update_fields=["estado"])
    return True


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
    queryset = Orden.objects.select_related("reporte")
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

    @action(detail=True, methods=["post"])
    def reporte(self, request, pk=None):
        if getattr(request.user, "rol", "") not in ("admin", "encargada", "reportes"):
            return Response(
                {"detail": "No tiene permiso para generar reportes."},
                status=status.HTTP_403_FORBIDDEN,
            )
        orden = self.get_object()
        existente = getattr(orden, "reporte", None)
        if existente is not None:
            return Response(
                self.get_serializer(orden).data["reporte"],
                status=status.HTTP_200_OK,
            )
        if orden.estado != Orden.Estado.VALIDADA:
            return Response(
                {"detail": "Solo se genera el reporte de una orden validada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reporte = Reporte(orden=orden, generado_por=request.user)
        try:
            with transaction.atomic():
                reporte.save()
                reporte.codigo_qr = f"LAB-{reporte.numero}"
                reporte.pdf.save(
                    f"{reporte.numero}.pdf", generar_pdf(orden, reporte), save=False
                )
                reporte.save(update_fields=["codigo_qr", "pdf"])
                orden.estado = Orden.Estado.PDF
                orden.save(update_fields=["estado"])
        except Exception:
            if reporte.pdf:
                reporte.pdf.delete(save=False)
            return Response(
                {"detail": "No se pudo generar el PDF del reporte."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "id": reporte.id,
                "numero": reporte.numero,
                "generado": reporte.generado.isoformat(),
                "pdf_url": f"/api/reportes/{reporte.id}/pdf/",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def entrega(self, request, pk=None):
        if getattr(request.user, "rol", "") not in ("admin", "encargada", "reportes"):
            return Response(
                {"detail": "No tiene permiso para registrar entregas."},
                status=status.HTTP_403_FORBIDDEN,
            )
        orden = self.get_object()
        reporte = getattr(orden, "reporte", None)
        if reporte is None or not reporte.pdf:
            return Response(
                {"detail": "Genere el reporte antes de registrar la entrega."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if reporte.entregado_at is not None or orden.estado == Orden.Estado.ENTREGADA:
            return Response(
                {"detail": "La orden ya fue entregada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if orden.estado != Orden.Estado.PDF:
            return Response(
                {"detail": "Solo se entrega una orden con reporte generado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        datos = request.data
        if not isinstance(datos, dict):
            return Response(
                {"detail": "Se esperaba un objeto JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        enviado_a = str(datos.get("enviado_a", "")).strip()
        if enviado_a:
            try:
                validate_email(enviado_a)
            except ValidationError:
                return Response(
                    {"enviado_a": ["Ingrese un correo válido."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            evento = EnvioReporte.objects.create(
                reporte=reporte, enviado_a=enviado_a, usuario=request.user
            )
            if not enviar_con_historial(orden, reporte, evento):
                return Response(
                    {"detail": "No se pudo enviar el correo del reporte."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
        reporte.enviado_a = enviado_a
        reporte.entregado_at = timezone.now()
        reporte.entregado_por = request.user
        reporte.save(update_fields=["enviado_a", "entregado_at", "entregado_por"])
        orden.estado = Orden.Estado.ENTREGADA
        orden.save(update_fields=["estado"])
        return Response(self.get_serializer(orden).data)


    @action(detail=True, methods=["get"])
    def envios(self, request, pk=None):
        if getattr(request.user, "rol", "") not in ("admin", "encargada", "reportes"):
            return Response({"detail": "No tiene permiso para consultar envíos."}, status=403)
        orden = self.get_object()
        eventos = EnvioReporte.objects.filter(reporte__orden=orden).select_related("usuario")
        page = self.paginate_queryset(eventos)
        return self.get_paginated_response(EnvioReporteSerializer(page, many=True).data)

    @action(detail=True, methods=["post"])
    def reenviar(self, request, pk=None):
        if getattr(request.user, "rol", "") not in ("admin", "encargada", "reportes"):
            return Response({"detail": "No tiene permiso para reenviar reportes."}, status=403)
        orden = self.get_object()
        reporte = getattr(orden, "reporte", None)
        if reporte is None or not reporte.pdf or reporte.entregado_at is None:
            return Response({"detail": "Registre la primera entrega antes de reenviar."}, status=400)
        datos = ReenvioSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        evento, created = EnvioReporte.objects.get_or_create(
            solicitud=datos.validated_data["solicitud"],
            defaults={
                "reporte": reporte, "usuario": request.user, "reenvio": True,
                "enviado_a": datos.validated_data["enviado_a"],
            },
        )
        if not created:
            if (
                evento.reporte_id != reporte.pk
                or evento.usuario_id != request.user.pk
                or evento.enviado_a != datos.validated_data["enviado_a"]
                or not evento.reenvio
                or evento.estado != EnvioReporte.Estado.ENVIADO
            ):
                return Response({"detail": "La solicitud ya fue utilizada; revise el historial."}, status=409)
            return Response(EnvioReporteSerializer(evento).data)
        if not enviar_con_historial(orden, reporte, evento):
            return Response({"detail": "No se pudo enviar el correo del reporte."}, status=502)
        return Response(EnvioReporteSerializer(evento).data, status=201)


class ReporteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reporte.objects.select_related("orden")
    serializer_class = ReporteSerializer
    search_fields = ["numero", "orden__numero"]

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        reporte = self.get_object()
        if not reporte.pdf or not reporte.pdf.storage.exists(reporte.pdf.name):
            return Response(
                {"detail": "El reporte todavía no tiene PDF."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return FileResponse(
            reporte.pdf.open("rb"),
            as_attachment=True,
            filename=f"{reporte.numero}.pdf",
        )
