from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from apps.usuarios.models import Turno
from apps.clientes.models import Cliente, Plan
from apps.pagos.models import Pago

User = get_user_model()


class Command(BaseCommand):
    help = "Carga datos de prueba: clientes con distintos estados de pago"

    def handle(self, *args, **options):
        self.stdout.write("Cargando datos de prueba...\n")

        # Obtener turnos
        turno_manana = Turno.objects.get(nombre="Mañana")
        turno_tarde = Turno.objects.get(nombre="Tarde")
        turno_noche = Turno.objects.get(nombre="Noche")

        # Obtener planes
        plan_3_dias = Plan.objects.get(codigo="3_dias")
        plan_5_dias = Plan.objects.get(codigo="5_dias")

        # Obtener usuario
        usuario = User.objects.filter(is_superuser=True).first()
        if not usuario:
            self.stdout.write(self.style.ERROR("No hay superuser. Creá uno primero."))
            return

        hoy = date.today()

        # --- TURNO MAÑANA ---
        self.stdout.write("\n📅 TURNO MAÑANA:")

        # Cliente 1: AL DÍA
        cliente1 = Cliente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            plan=plan_3_dias,
            telefono="1234567890",
            email="juan@mail.com",
            turno=turno_manana,
            activo=True,
            usuario_creador=usuario,
        )
        Pago.objects.create(
            cliente=cliente1,
            fecha_pago=hoy - timedelta(days=5),
            mes_cubierto=hoy.replace(day=1),
            monto=8000,
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ✅ {cliente1.nombre} {cliente1.apellido} - AL DÍA")

        # Cliente 2: AL DÍA
        cliente2 = Cliente.objects.create(
            nombre="María",
            apellido="González",
            plan=plan_5_dias,
            telefono="0987654321",
            email="maria@mail.com",
            turno=turno_manana,
            activo=True,
            usuario_creador=usuario,
        )
        Pago.objects.create(
            cliente=cliente2,
            fecha_pago=hoy,
            mes_cubierto=hoy.replace(day=1),
            monto=12000,
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ✅ {cliente2.nombre} {cliente2.apellido} - AL DÍA")

        # Cliente 3: VENCIDO
        cliente3 = Cliente.objects.create(
            nombre="Carlos",
            apellido="Rodríguez",
            plan=plan_3_dias,
            telefono="1122334455",
            turno=turno_manana,
            activo=True,
            usuario_creador=usuario,
        )
        mes_pasado = hoy - relativedelta(months=1)
        Pago.objects.create(
            cliente=cliente3,
            fecha_pago=mes_pasado,
            mes_cubierto=mes_pasado.replace(day=1),
            monto=8000,
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ❌ {cliente3.nombre} {cliente3.apellido} - VENCIDO")

        # Cliente 4: AL DÍA (si es antes del 10)
        if hoy.day <= 10:
            cliente4 = Cliente.objects.create(
                nombre="Ana",
                apellido="Martínez",
                plan=plan_5_dias,
                telefono="5566778899",
                turno=turno_manana,
                activo=True,
                usuario_creador=usuario,
            )
            self.stdout.write(f"  ⏳ {cliente4.nombre} {cliente4.apellido} - AL DÍA")

        # --- TURNO TARDE ---
        self.stdout.write("\n📅 TURNO TARDE:")

        # Cliente 5: AL DÍA
        cliente5 = Cliente.objects.create(
            nombre="Luis",
            apellido="Fernández",
            plan=plan_3_dias,
            telefono="9988776655",
            turno=turno_tarde,
            activo=True,
            usuario_creador=usuario,
        )
        Pago.objects.create(
            cliente=cliente5,
            fecha_pago=hoy - timedelta(days=2),
            mes_cubierto=hoy.replace(day=1),
            monto=8000,
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ✅ {cliente5.nombre} {cliente5.apellido} - AL DÍA")

        # Cliente 6: VENCIDO
        cliente6 = Cliente.objects.create(
            nombre="Laura",
            apellido="Sánchez",
            plan=plan_5_dias,
            telefono="4433221100",
            turno=turno_tarde,
            activo=True,
            usuario_creador=usuario,
        )
        mes_pasado = hoy - relativedelta(months=1)
        Pago.objects.create(
            cliente=cliente6,
            fecha_pago=mes_pasado - timedelta(days=10),
            mes_cubierto=mes_pasado.replace(day=1),
            monto=12000,
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ❌ {cliente6.nombre} {cliente6.apellido} - VENCIDO")

        # Cliente 7: PENDIENTE CONSULTA
        cliente7 = Cliente.objects.create(
            nombre="Pedro",
            apellido="Ramírez",
            plan=plan_3_dias,
            telefono="6677889900",
            turno=turno_tarde,
            activo=True,
            estado_consulta="pendiente",
            fecha_ultima_consulta=hoy,
            usuario_creador=usuario,
        )
        hace_3_meses = hoy - relativedelta(months=3)
        Pago.objects.create(
            cliente=cliente7,
            fecha_pago=hace_3_meses,
            mes_cubierto=hace_3_meses.replace(day=1),
            monto=8000,
            usuario_registrador=usuario,
        )
        self.stdout.write(
            f"  ⚠️  {cliente7.nombre} {cliente7.apellido} - PENDIENTE CONSULTA"
        )

        # --- TURNO NOCHE ---
        self.stdout.write("\n📅 TURNO NOCHE:")

        # Cliente 8: AL DÍA
        cliente8 = Cliente.objects.create(
            nombre="Sofía",
            apellido="Torres",
            plan=plan_5_dias,
            telefono="3344556677",
            turno=turno_noche,
            activo=True,
            usuario_creador=usuario,
        )
        Pago.objects.create(
            cliente=cliente8,
            fecha_pago=hoy - timedelta(days=1),
            mes_cubierto=hoy.replace(day=1),
            monto=12000,
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ✅ {cliente8.nombre} {cliente8.apellido} - AL DÍA")

        # Cliente 9: VENCIDO
        cliente9 = Cliente.objects.create(
            nombre="Diego",
            apellido="Morales",
            plan=plan_3_dias,
            telefono="7788990011",
            turno=turno_noche,
            activo=True,
            usuario_creador=usuario,
        )
        self.stdout.write(f"  ❌ {cliente9.nombre} {cliente9.apellido} - VENCIDO")

        # Cliente 10: AL DÍA (pago proporcional)
        cliente10 = Cliente.objects.create(
            nombre="Valentina",
            apellido="Castro",
            plan=plan_5_dias,
            telefono="2233445566",
            turno=turno_noche,
            activo=True,
            usuario_creador=usuario,
        )
        Pago.objects.create(
            cliente=cliente10,
            fecha_pago=hoy,
            mes_cubierto=hoy.replace(day=1),
            monto=6000,
            observaciones="Pago proporcional - ingresó el día 20",
            usuario_registrador=usuario,
        )
        self.stdout.write(f"  ✅ {cliente10.nombre} {cliente10.apellido} - AL DÍA")

        # Cliente 11: INACTIVO
        cliente11 = Cliente.objects.create(
            nombre="Roberto",
            apellido="Vargas",
            plan=plan_3_dias,
            telefono="8899001122",
            turno=turno_noche,
            activo=False,
            usuario_creador=usuario,
        )
        self.stdout.write(f"  🚫 {cliente11.nombre} {cliente11.apellido} - INACTIVO")

        self.stdout.write(
            self.style.SUCCESS("\n✅ Datos de prueba cargados exitosamente!")
        )
        self.stdout.write(f"\nTotal clientes: {Cliente.objects.count()}")
        self.stdout.write(f"Total pagos: {Pago.objects.count()}")
