from django.core.management.base import BaseCommand
from apps.clientes.models import Plan


class Command(BaseCommand):
    help = "Crea los planes iniciales del gimnasio"

    def handle(self, *args, **options):
        planes = [
            {
                "codigo": "3_dias",
                "nombre": "3 días por semana",
                "precio": 8000,
                "orden": 1,
            },
            {
                "codigo": "5_dias",
                "nombre": "5 días por semana",
                "precio": 12000,
                "orden": 2,
            },
        ]

        for plan_data in planes:
            plan, created = Plan.objects.get_or_create(
                codigo=plan_data["codigo"],
                defaults={
                    "nombre": plan_data["nombre"],
                    "precio": plan_data["precio"],
                    "orden": plan_data["orden"],
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Plan creado: {plan}"))
            else:
                self.stdout.write(f"Plan ya existe: {plan}")
