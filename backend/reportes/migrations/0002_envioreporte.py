import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reportes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EnvioReporte",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("solicitud", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("enviado_a", models.EmailField(max_length=254)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"), ("enviado", "Aceptado por el servidor de correo"), ("fallido", "Fallido")], default="pendiente", max_length=10)),
                ("reenvio", models.BooleanField(default=False)),
                ("reporte", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="envios", to="reportes.reporte")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-fecha", "-pk"]},
        ),
    ]
