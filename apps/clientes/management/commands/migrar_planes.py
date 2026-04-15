from django.core.management.base import BaseCommand
from apps.clientes.models import Cliente, Plan


class Command(BaseCommand):
    help = "Migra clientes de plan CharField a plan FK"

    def handle(self, *args, **options):
        # Mapeo de códigos viejos a nuevos
        mapeo = {
            "3_dias": "3_dias",
            "5_dias": "5_dias",
        }

        clientes = Cliente.objects.all()
        migrados = 0
        errores = 0

        for cliente in clientes:
            codigo_viejo = cliente.plan
            codigo_nuevo = mapeo.get(codigo_viejo)

            if codigo_nuevo:
                try:
                    plan_obj = Plan.objects.get(codigo=codigo_nuevo)
                    cliente.plan_nuevo = plan_obj
                    cliente.save(update_fields=["plan_nuevo"])
                    migrados += 1
                    self.stdout.write(
                        f"✅ {cliente.apellido}, {cliente.nombre}: {codigo_viejo} → {plan_obj}"
                    )
                except Plan.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Plan no encontrado: {codigo_nuevo}")
                    )
                    errores += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  {cliente.apellido}: código desconocido "{codigo_viejo}"'
                    )
                )
                errores += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ Migrados: {migrados}"))
        if errores:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errores}"))
