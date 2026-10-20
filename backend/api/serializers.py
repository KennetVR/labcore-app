from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from catalogo.models import (
    Cliente,
    Examen,
    Paquete,
    PaqueteExamen,
    TarifarioExamen,
    TarifarioPaquete,
    Zona,
)
from ordenes.models import Orden, OrdenItem
from pacientes.models import Paciente
from reportes.models import EnvioReporte, Reporte


class ReenvioSerializer(serializers.Serializer):
    enviado_a = serializers.EmailField(max_length=254)
    solicitud = serializers.UUIDField()


class EnvioReporteSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = EnvioReporte
        fields = ["id", "enviado_a", "usuario", "fecha", "estado", "reenvio"]


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = ["id", "nombre", "activo"]


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nombre", "tipo", "zona", "contacto", "activo"]


class ExamenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Examen
        fields = [
            "id",
            "codigo",
            "nombre",
            "area",
            "resultado_tipo",
            "unidad",
            "metodo",
            "ref_min",
            "ref_max",
            "ref_texto",
            "mide_pre_post",
            "activo",
        ]


class PaqueteExamenesField(serializers.Field):
    def to_representation(self, value):
        return [
            {"orden": pe.orden, "examen": pe.examen_id}
            for pe in value.all()
        ]

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError("Se esperaba una lista de exámenes.")
        members = []
        for index, entry in enumerate(data):
            if isinstance(entry, dict):
                exam_id = entry.get("examen")
                orden = entry.get("orden", index)
            else:
                exam_id, orden = entry, index
            if isinstance(exam_id, bool) or not isinstance(exam_id, int):
                raise serializers.ValidationError(
                    "Cada examen debe indicar su id numérico."
                )
            if isinstance(orden, bool) or not isinstance(orden, int) or orden < 0:
                raise serializers.ValidationError(
                    "El orden de cada examen debe ser un entero no negativo."
                )
            members.append((exam_id, orden))
        exam_ids = [exam_id for exam_id, _ in members]
        if len(set(exam_ids)) != len(exam_ids):
            raise serializers.ValidationError(
                "No se puede repetir un examen en el paquete."
            )
        existentes = set(
            Examen.objects.filter(id__in=exam_ids).values_list("id", flat=True)
        )
        faltantes = [exam_id for exam_id in exam_ids if exam_id not in existentes]
        if faltantes:
            raise serializers.ValidationError(f"Exámenes inexistentes: {faltantes}.")
        return members


class PaqueteSerializer(serializers.ModelSerializer):
    examenes = PaqueteExamenesField(source="examenes_compuestos", required=False)

    class Meta:
        model = Paquete
        fields = ["id", "nombre", "frecuencia", "activo", "examenes"]

    def _sync_miembros(self, paquete, members):
        paquete.examenes_compuestos.all().delete()
        PaqueteExamen.objects.bulk_create(
            [
                PaqueteExamen(paquete=paquete, examen_id=exam_id, orden=orden)
                for exam_id, orden in members
            ]
        )

    def create(self, validated_data):
        members = validated_data.pop("examenes_compuestos", None)
        with transaction.atomic():
            paquete = super().create(validated_data)
            if members is not None:
                self._sync_miembros(paquete, members)
        return paquete

    def update(self, instance, validated_data):
        members = validated_data.pop("examenes_compuestos", None)
        with transaction.atomic():
            paquete = super().update(instance, validated_data)
            if members is not None:
                self._sync_miembros(paquete, members)
        return paquete


class TarifarioExamenSerializer(serializers.ModelSerializer):
    examen_codigo = serializers.CharField(source="examen.codigo", read_only=True)
    examen_nombre = serializers.CharField(source="examen.nombre", read_only=True)
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)

    class Meta:
        model = TarifarioExamen
        fields = [
            "id",
            "examen",
            "examen_codigo",
            "examen_nombre",
            "precio",
            "zona",
            "zona_nombre",
            "cliente",
            "cliente_nombre",
            "vigencia_desde",
            "activo",
        ]


class TarifarioPaqueteSerializer(serializers.ModelSerializer):
    paquete_nombre = serializers.CharField(source="paquete.nombre", read_only=True)
    zona_nombre = serializers.CharField(source="zona.nombre", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)

    class Meta:
        model = TarifarioPaquete
        fields = [
            "id",
            "paquete",
            "paquete_nombre",
            "precio",
            "zona",
            "zona_nombre",
            "cliente",
            "cliente_nombre",
            "vigencia_desde",
            "activo",
        ]


class ReporteSerializer(serializers.ModelSerializer):
    orden_numero = serializers.CharField(source="orden.numero", read_only=True)
    pdf_url = serializers.SerializerMethodField()
    entregado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = [
            "id",
            "numero",
            "orden",
            "orden_numero",
            "generado",
            "codigo_qr",
            "pdf_url",
            "enviado_a",
            "entregado_at",
            "entregado_por",
            "entregado_por_nombre",
        ]

    def get_pdf_url(self, obj):
        return f"/api/reportes/{obj.id}/pdf/" if obj.pdf else None

    def get_entregado_por_nombre(self, obj):
        if obj.entregado_por is None:
            return None
        return obj.entregado_por.get_full_name() or obj.entregado_por.username


class PacienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Paciente
        fields = [
            "id",
            "dni",
            "apellidos",
            "nombres",
            "sexo",
            "fecha_nacimiento",
            "cliente",
            "observaciones",
            "nombre_completo",
        ]


class OrdenItemSerializer(serializers.ModelSerializer):
    examen = serializers.PrimaryKeyRelatedField(queryset=Examen.objects.all())
    paquete = serializers.PrimaryKeyRelatedField(
        queryset=Paquete.objects.all(), allow_null=True, required=False
    )
    examen_codigo = serializers.CharField(source="examen.codigo", read_only=True)
    examen_nombre = serializers.CharField(source="examen.nombre", read_only=True)
    paquete_nombre = serializers.CharField(
        source="paquete.nombre", read_only=True, default=""
    )

    def validate(self, attrs):
        paquete = attrs.get("paquete")
        if paquete and not paquete.examenes_compuestos.filter(examen=attrs["examen"]).exists():
            raise serializers.ValidationError({"examen": "El examen no pertenece al paquete seleccionado."})
        return attrs

    class Meta:
        model = OrdenItem
        fields = [
            "id",
            "paquete",
            "paquete_nombre",
            "examen",
            "examen_codigo",
            "examen_nombre",
            "cantidad",
            "medicion",
            "resultado",
            "bandera",
            "validado_por",
            "validado_at",
        ]
        read_only_fields = ["validado_por", "validado_at"]


class OrdenSerializer(serializers.ModelSerializer):
    items = OrdenItemSerializer(many=True, required=False)
    total = serializers.SerializerMethodField()
    reporte = serializers.SerializerMethodField()
    paciente_nombre = serializers.CharField(
        source="paciente.nombre_completo", read_only=True, default=""
    )
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True, default="")

    class Meta:
        model = Orden
        fields = [
            "id",
            "numero",
            "paciente",
            "cliente",
            "paciente_nombre",
            "cliente_nombre",
            "estado",
            "solicitado_por",
            "observacion",
            "fecha",
            "items",
            "total",
            "reporte",
        ]
        read_only_fields = ["numero", "fecha", "creado_por"]

    def get_total(self, obj):
        total = obj.calcular_total()
        return str(total) if total is not None else None

    def get_reporte(self, obj):
        reporte = getattr(obj, "reporte", None)
        if reporte is None or not reporte.pdf:
            return None
        return {
            "id": reporte.id,
            "numero": reporte.numero,
            "generado": reporte.generado.isoformat(),
            "pdf_url": f"/api/reportes/{reporte.id}/pdf/",
            "enviado_a": reporte.enviado_a,
            "entregado_at": (
                reporte.entregado_at.isoformat() if reporte.entregado_at else None
            ),
            "entregado_por": (
                reporte.entregado_por.get_full_name()
                or reporte.entregado_por.username
                if reporte.entregado_por
                else None
            ),
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.quotation = self.quote(attrs)
        return attrs

    def quote(self, attrs):
        items = attrs.get("items", [])
        cliente = attrs.get("cliente", self.instance.cliente if self.instance else None)
        orden = Orden(cliente=cliente)
        if self.instance:
            orden.fecha = self.instance.fecha
        errores = []
        lines = []
        total = Decimal("0.00")

        for item in items:
            paquete = item.get("paquete")
            examen = item["examen"]
            precio = orden._tarifa(paquete=paquete) if paquete else orden._tarifa(examen=examen)
            if precio is None:
                recurso = f"el paquete {paquete.nombre}" if paquete else f"el examen {examen.codigo}"
                errores.append(f"No hay una tarifa vigente para {recurso}.")
            else:
                errores.append({})
                subtotal = (precio * item.get("cantidad", 1)).quantize(Decimal("0.01"))
                lines.append({"precio_unitario": str(precio), "subtotal": str(subtotal)})
                total += subtotal

        if any(errores):
            raise serializers.ValidationError({"items": errores})
        return {"items": lines, "total": str(total)}

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        orden = Orden.objects.create(**validated_data)
        for item in items:
            OrdenItem.objects.create(orden=orden, **item)
        return orden
