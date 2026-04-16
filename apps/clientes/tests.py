from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from datetime import date

from apps.usuarios.models import Turno
from apps.clientes.models import Cliente, Plan
from apps.pagos.models import Pago
from apps.clientes.services import calcular_estado_cliente, marcar_clientes_inactivos

User = get_user_model()


class BaseTestCase(TestCase):
    """Setup común para todos los tests"""

    def setUp(self):
        self.turno = Turno.objects.create(
            nombre="Mañana", hora_inicio="07:30", hora_fin="11:00", activo=True
        )
        self.usuario = User.objects.create_user(username="testuser", password="test123")
        self.plan = Plan.objects.create(
            codigo="3_dias", nombre="3 veces por semana", precio=35000, activo=True
        )
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            plan=self.plan,
            turno=self.turno,
            activo=True,
            usuario_creador=self.usuario,
        )


class EstadoClienteTestCase(BaseTestCase):
    """Tests para calcular_estado_cliente"""

    def test_cliente_inactivo(self):
        self.cliente.activo = False
        self.cliente.save()
        self.assertEqual(calcular_estado_cliente(self.cliente), "inactivo")

    def test_cliente_con_pago_mes_actual(self):
        hoy = date(2026, 4, 15)
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=hoy,
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        self.assertEqual(calcular_estado_cliente(self.cliente, hoy), "al_dia")

    def test_cliente_sin_pago_antes_del_10(self):
        hoy = date(2026, 4, 8)
        self.assertEqual(calcular_estado_cliente(self.cliente, hoy), "al_dia")

    def test_cliente_sin_pago_despues_del_10(self):
        hoy = date(2026, 4, 15)
        self.assertEqual(calcular_estado_cliente(self.cliente, hoy), "vencido")

    def test_cliente_pendiente_consulta(self):
        # Pagó febrero, hoy es 11 de mayo → 2 meses desde vencimiento (10 marzo)
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 2, 15),
            mes_cubierto=date(2026, 2, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        hoy = date(2026, 5, 11)
        self.assertEqual(
            calcular_estado_cliente(self.cliente, hoy), "pendiente_consulta"
        )

    def test_cliente_vencido_no_llega_a_pendiente(self):
        # Pagó febrero, hoy es 10 de mayo → aún no llega a pendiente (necesita día 11)
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 2, 15),
            mes_cubierto=date(2026, 2, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        hoy = date(2026, 5, 10)
        self.assertEqual(calcular_estado_cliente(self.cliente, hoy), "al_dia")


class MarcarInactivosTestCase(BaseTestCase):
    """Tests para marcar_clientes_inactivos"""

    def test_marcar_cliente_pendiente(self):
        # Pagó febrero
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 2, 15),
            mes_cubierto=date(2026, 2, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        # Mockeamos date.today() para que sea 11 de mayo
        with patch("apps.clientes.services.date") as mock_date:
            mock_date.today.return_value = date(2026, 5, 11)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            marcados = marcar_clientes_inactivos()

        self.assertEqual(marcados, 1)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado_consulta, "pendiente")

    def test_no_marca_cliente_al_dia(self):
        # Pagó este mes
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        with patch("apps.clientes.services.date") as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            marcados = marcar_clientes_inactivos()

        self.assertEqual(marcados, 0)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.estado_consulta, "ninguno")


# Tests vistas
class DashboardViewTestCase(BaseTestCase):
    """Tests para la vista dashboard"""

    def test_redirige_sin_login(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_dashboard_con_login(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_filtra_por_turno(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get(f"/?turno={self.turno.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.cliente, response.context["clientes"])

    def test_dashboard_htmx_devuelve_partial(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get("/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/_tabla_clientes.html")


class ReportesViewTestCase(BaseTestCase):
    """Tests para la vista reportes — solo dueño"""

    def setUp(self):
        super().setUp()
        self.dueno = User.objects.create_user(
            username="dueno", password="dueno123", rol="dueño"
        )

    def test_profesor_no_puede_ver_reportes(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get("/reportes/")
        self.assertEqual(response.status_code, 403)

    def test_dueno_puede_ver_reportes(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/reportes/")
        self.assertEqual(response.status_code, 200)

    def test_sin_login_redirige(self):
        response = self.client.get("/reportes/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_reportes_contiene_datos_turnos(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/reportes/")
        self.assertIn("datos_turnos", response.context)


class CrearClienteViewTestCase(BaseTestCase):
    """Tests para crear cliente"""

    def test_get_modal_crear_cliente(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get("/crear/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/_modal_cliente.html")

    def test_crear_cliente_valido(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.post(
            "/crear/",
            {
                "nombre": "Pedro",
                "apellido": "Ramirez",
                "plan": self.plan.id,
                "turno": self.turno.id,
                "telefono": "3624000000",
                "email": "",
            },
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(Cliente.objects.filter(apellido="Ramirez").exists())

    def test_crear_cliente_invalido(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.post(
            "/crear/",
            {
                "nombre": "",
                "apellido": "",
                "plan": self.plan.id,
                "turno": self.turno.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Cliente.objects.filter(nombre="").exists())
