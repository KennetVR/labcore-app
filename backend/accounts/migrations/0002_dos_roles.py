from django.db import migrations, models

# Los roles que existieron antes de la política de dos roles. En un laboratorio
# con un solo rol operativo, esas cuentas pasan a "encargada" conservando su
# usuario y todo su historial; no se elimina ninguna cuenta.
ROLES_ELIMINADOS = ("auxiliar", "reportes", "muestreo")


def unificar_roles(apps, schema_editor):
    Usuario = apps.get_model("accounts", "Usuario")
    Usuario.objects.filter(rol__in=ROLES_ELIMINADOS).update(rol="encargada")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(unificar_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[("admin", "Administrador"), ("encargada", "Encargado")],
                default="encargada",
                max_length=20,
            ),
        ),
    ]
