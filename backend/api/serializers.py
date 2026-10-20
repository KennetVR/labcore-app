from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from catalogo.models import (
    Cliente,
    Examen,
    Paquete,
    TarifarioExamen,
    TarifarioPaquete,
    Zona,
)
from ordenes.models import Orden, OrdenItem
from pacientes.models import Paciente


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


class PaqueteSerializer(serializers.ModelSerializer):
    examenes = serializers.SerializerMethodField()

    class Meta:
        model = Paquete
        fields = ["id", "nombre", "frecuencia", "activo", "examenes"]

    def get_examenes(self, obj):
        return [
            {"orden": pe.orden, "examen": pe.examen_id}
            for pe in obj.examenes_compuestos.all()
        ]


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
        ]
        read_only_fields = ["numero", "fecha", "creado_por"]

    def get_total(self, obj):
        total = obj.calcular_total()
        return str(total) if total is not None else None

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
