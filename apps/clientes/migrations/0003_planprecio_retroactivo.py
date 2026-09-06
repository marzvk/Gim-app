from datetime import date

from django.db import migrations


def backfill_planprecio(apps, schema_editor):
    """Respalda el precio actual de cada plan como su precio histórico inicial."""
    Plan = apps.get_model("clientes", "Plan")
    PlanPrecio = apps.get_model("clientes", "PlanPrecio")
    for plan in Plan.objects.all():
        PlanPrecio.objects.get_or_create(
            plan=plan,
            vigencia_desde=date(2020, 1, 1),
            defaults={"precio": plan.precio},
        )


def reverse(apps, schema_editor):
    PlanPrecio = apps.get_model("clientes", "PlanPrecio")
    PlanPrecio.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0002_planprecio"),
    ]

    operations = [
        migrations.RunPython(backfill_planprecio, reverse),
    ]