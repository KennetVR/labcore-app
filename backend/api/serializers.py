from rest_framework import serializers

from catalogo.models import Cliente, Examen, Paquete, Zona
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

    class Meta:
        model = OrdenItem
        fields = [
            "id",
            "paquete",
            "examen",
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
        return str(obj.calcular_total())

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        orden = Orden.objects.create(**validated_data)
        for item in items:
            OrdenItem.objects.create(orden=orden, **item)
        return orden