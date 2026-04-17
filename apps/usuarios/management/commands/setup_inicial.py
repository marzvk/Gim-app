from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.usuarios.models import Turno
from apps.clientes.models import Plan

User = get_user_model()


class Command(BaseCommand):
    help = "Crea datos iniciales: turnos, planes y usuario admin"

    def handle(self, *args, **kwargs):

        # Turnos
        turnos = [
            {"nombre": "Mañana", "hora_inicio": "07:30", "hora_fin": "11:00"},
            {"nombre": "Tarde", "hora_inicio": "14:00", "hora_fin": "19:00"},
            {"nombre": "Noche", "hora_inicio": "19:00", "hora_fin": "23:00"},
        ]
        for t in turnos:
            obj, created = Turno.objects.get_or_create(
                nombre=t["nombre"],
                defaults={
                    "hora_inicio": t["hora_inicio"],
                    "hora_fin": t["hora_fin"],
                    "activo": True,
                },
            )
            if created:
                self.stdout.write(f"  Turno creado: {obj.nombre}")
            else:
                self.stdout.write(f"  Turno ya existe: {obj.nombre}")

        # Planes
        planes = [
            {
                "codigo": "3_dias",
                "nombre": "3 veces por semana",
                "precio": 35000,
                "orden": 1,
            },
            {
                "codigo": "5_dias",
                "nombre": "5 veces por semana",
                "precio": 45000,
                "orden": 2,
            },
            {"codigo": "libre", "nombre": "Libre", "precio": 55000, "orden": 3},
        ]
        for p in planes:
            obj, created = Plan.objects.get_or_create(
                codigo=p["codigo"],
                defaults={
                    "nombre": p["nombre"],
                    "precio": p["precio"],
                    "activo": True,
                    "orden": p["orden"],
                },
            )
            if created:
                self.stdout.write(f"  Plan creado: {obj.nombre}")
            else:
                self.stdout.write(f"  Plan ya existe: {obj.nombre}")

        # Usuario admin
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                password="admin1234",
                email="",
                rol="dueño",
            )
            self.stdout.write("  Usuario admin creado (cambiá la contraseña!)")
        else:
            self.stdout.write("  Usuario admin ya existe")

        self.stdout.write(self.style.SUCCESS("Setup inicial completado."))
