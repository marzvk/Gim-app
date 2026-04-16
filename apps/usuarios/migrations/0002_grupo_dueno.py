from django.db import migrations


def crear_grupo_dueno(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    grupo, _ = Group.objects.get_or_create(name="Dueño")

    # Permisos permitidos para el dueño
    codenames = [
        # Planes
        "add_plan",
        "change_plan",
        "view_plan",
        # Turnos
        "change_turno",
        "view_turno",
        # Usuarios (solo ver y crear profesores)
        "add_usuario",
        "change_usuario",
        "view_usuario",
        # Clientes (ver)
        "view_cliente",
    ]

    permisos = Permission.objects.filter(codename__in=codenames)
    grupo.permissions.set(permisos)


def eliminar_grupo_dueno(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Dueño").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
        ("clientes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_grupo_dueno, eliminar_grupo_dueno),
    ]
