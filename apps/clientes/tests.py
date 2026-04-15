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
