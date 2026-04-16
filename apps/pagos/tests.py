from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date

from apps.usuarios.models import Turno
from apps.clientes.models import Cliente, Plan
from apps.pagos.models import Pago
from apps.pagos.forms import PagoEditarForm

User = get_user_model()


class BaseTestCase(TestCase):

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


class PagoFormTestCase(BaseTestCase):

    def test_form_valido(self):
        pago_instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={"mes_cubierto": "2026-04", "monto": "35000", "observaciones": ""},
            instance=pago_instancia,
        )
        self.assertTrue(form.is_valid())

    def test_mes_cubierto_se_normaliza_a_dia_1(self):
        pago_instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={"mes_cubierto": "2026-04", "monto": "35000", "observaciones": ""},
            instance=pago_instancia,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["mes_cubierto"], date(2026, 4, 1))

    def test_monto_cero_invalido(self):
        pago_instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={"mes_cubierto": "2026-04", "monto": "0", "observaciones": ""},
            instance=pago_instancia,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("monto", form.errors)

    def test_monto_negativo_invalido(self):
        pago_instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={"mes_cubierto": "2026-04", "monto": "-100", "observaciones": ""},
            instance=pago_instancia,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("monto", form.errors)

    def test_duplicado_mismo_mes_invalido(self):
        # Pago existente para abril
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        # Intentar crear otro pago para abril
        pago_instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={"mes_cubierto": "2026-04", "monto": "35000", "observaciones": ""},
            instance=pago_instancia,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("mes_cubierto", form.errors)

    def test_editar_pago_no_cuenta_como_duplicado(self):
        # Pago existente para abril
        pago = Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        # Editar ese mismo pago con mismo mes → no debe dar error de duplicado
        form = PagoEditarForm(
            data={"mes_cubierto": "2026-04", "monto": "40000", "observaciones": ""},
            instance=pago,
        )
        self.assertTrue(form.is_valid())

    def test_mes_cubierto_invalido(self):
        pago_instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={"mes_cubierto": "fecha-mala", "monto": "35000", "observaciones": ""},
            instance=pago_instancia,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("mes_cubierto", form.errors)


# Test registrar pagos


class RegistrarPagoViewTestCase(BaseTestCase):
    """Tests para la vista modal_registrar_pago"""

    def test_redirige_sin_login(self):
        response = self.client.get(f"/pagos/pago/{self.cliente.id}/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_get_modal_pago(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get(f"/pagos/pago/{self.cliente.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pagos/_modal_pago.html")

    def test_registrar_pago_valido(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.post(
            f"/pagos/pago/{self.cliente.id}/",
            {
                "mes_cubierto": "2026-04",
                "monto": "35000",
                "observaciones": "",
            },
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(Pago.objects.filter(cliente=self.cliente).exists())

    def test_no_permite_pago_duplicado(self):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        self.client.login(username="testuser", password="test123")
        response = self.client.post(
            f"/pagos/pago/{self.cliente.id}/",
            {
                "mes_cubierto": "2026-04",
                "monto": "35000",
                "observaciones": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pago.objects.filter(cliente=self.cliente).count(), 1)


class EditarPagoViewTestCase(BaseTestCase):
    """Tests para la vista editar_pago"""

    def setUp(self):
        super().setUp()
        self.pago = Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )

    def test_get_modal_editar(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get(f"/pagos/editar/{self.pago.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pagos/_modal_editar_pago.html")

    def test_editar_pago_valido(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.post(
            f"/pagos/editar/{self.pago.id}/",
            {
                "mes_cubierto": "2026-04",
                "monto": "40000",
                "observaciones": "Editado",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.monto, 40000)


class BorrarPagoViewTestCase(BaseTestCase):
    """Tests para la vista borrar_pago"""

    def setUp(self):
        super().setUp()
        self.pago = Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )

    def test_borrar_pago(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.post(f"/pagos/borrar/{self.pago.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Pago.objects.filter(id=self.pago.id).exists())

    def test_get_no_permitido(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get(f"/pagos/borrar/{self.pago.id}/")
        self.assertEqual(response.status_code, 405)
