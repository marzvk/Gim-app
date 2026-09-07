from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from datetime import date
import os

from apps.usuarios.models import Turno
from apps.clientes.models import Cliente, Plan, PlanPrecio
from apps.pagos.models import Pago
from apps.clientes.services import (
    calcular_estado_cliente,
    marcar_clientes_inactivos,
    clientes_no_al_dia,
    montos_del_mes,
)

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
@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
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


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
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


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
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


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class AccionesClienteViewTestCase(BaseTestCase):
    """Tests para el menú de acciones del cliente (mobile)"""

    def test_get_modal_acciones(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get(f"/cliente/{self.cliente.id}/acciones/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/_modal_acciones.html")
        self.assertContains(response, self.cliente.apellido)

    def test_sin_clientes_404(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get("/cliente/9999/acciones/")
        self.assertEqual(response.status_code, 404)


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class NotificacionesNoAlDiaTestCase(BaseTestCase):
    """Tests de notificaciones: clientes sin completar el mes (vencido o parcial)"""

    def setUp(self):
        super().setUp()
        self.turno2 = Turno.objects.create(
            nombre="Tarde", hora_inicio="14:00", hora_fin="19:00", activo=True
        )
        self.dueno = User.objects.create_user(
            username="dueno", password="dueno123", rol="dueño"
        )
        self.profesor = User.objects.create_user(
            username="profesor",
            password="prof123",
            rol="profesor",
            turno_asignado=self.turno,
        )
        self.cliente2 = Cliente.objects.create(
            nombre="Ana",
            apellido="Gómez",
            plan=self.plan,
            turno=self.turno2,
            activo=True,
            usuario_creador=self.usuario,
        )

    def _mock_hoy(self):
        return patch("apps.clientes.services.date")

    def test_no_al_dia_dueño_todos(self):
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            self.assertEqual(len(clientes_no_al_dia(self.dueno)), 2)

    def test_no_al_dia_profesor_solo_su_turno(self):
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            clientes = clientes_no_al_dia(self.profesor)
            self.assertEqual(len(clientes), 1)
            self.assertEqual(clientes[0].pk, self.cliente.pk)

    def test_no_al_dia_profesor_sin_turno_vacio(self):
        profesor_sin_turno = User.objects.create_user(
            username="profesor2", password="prof123", rol="profesor"
        )
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            self.assertEqual(clientes_no_al_dia(profesor_sin_turno), [])

    def test_parcial_cuenta_como_no_al_dia(self):
        Pago.objects.create(
            cliente=self.cliente2,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            clientes = clientes_no_al_dia(self.dueno)
        self.assertEqual(len(clientes), 2)
        parcial = next(c for c in clientes if c.pk == self.cliente2.pk)
        self.assertEqual(parcial.estado_actual, "deuda_parcial")
        self.assertEqual(parcial.monto_debido, 15000)

    def test_pago_completo_saca_de_la_lista(self):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            self.assertEqual(len(clientes_no_al_dia(self.dueno)), 1)

    def test_badge_cuenta_vencido_y_parcial(self):
        Pago.objects.create(
            cliente=self.cliente2,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        self.client.login(username="dueno", password="dueno123")
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = self.client.get("/")
        self.assertEqual(response.context["cantidad_no_al_dia"], 2)
        self.assertContains(response, "notif-badge")

    def test_modal_dueño_muestra_todos_los_turnos(self):
        self.client.login(username="dueno", password="dueno123")
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = self.client.get("/notificaciones/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/_modal_notificaciones.html")
        self.assertContains(response, "Pérez,")
        self.assertContains(response, "Gómez,")

    def test_modal_profesor_solo_su_turno(self):
        self.client.login(username="profesor", password="prof123")
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = self.client.get("/notificaciones/")
        self.assertContains(response, "Pérez,")
        self.assertNotContains(response, "Gómez,")

    def test_modal_muestra_a_debe_parcial(self):
        Pago.objects.create(
            cliente=self.cliente2,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        self.client.login(username="dueno", password="dueno123")
        with self._mock_hoy() as mock_date:
            mock_date.today.return_value = date(2026, 4, 15)
            mock_date.side_effect = lambda *a, **kw: date(*a, **kw)
            response = self.client.get("/notificaciones/")
        self.assertContains(response, "Aún debe")
        self.assertContains(response, "$15000")

    def test_modal_sin_pendientes_muestra_vacio(self):
        profesor_sin_turno = User.objects.create_user(
            username="profesor3", password="prof123", rol="profesor"
        )
        self.client.login(username="profesor3", password="prof123")
        response = self.client.get("/notificaciones/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sin clientes sin pagar")


class PrecioVigenteTestCase(BaseTestCase):
    """Los cambios de precio aplican desde el próximo mes, no son retroactivos."""

    def _cambio_precio_proximo_mes(self, precio=40000):
        PlanPrecio.objects.create(
            plan=self.plan, precio=precio, vigencia_desde=date(2026, 5, 1)
        )

    def test_precio_nuevo_aplica_desde_mes_siguiente(self):
        self._cambio_precio_proximo_mes()
        self.assertEqual(montos_del_mes(self.cliente, date(2026, 4, 15)), (0, 35000))
        self.assertEqual(montos_del_mes(self.cliente, date(2026, 5, 15)), (0, 40000))
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 5, 15)), "vencido"
        )

    def test_cambio_precio_no_genera_deuda_retroactiva(self):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.usuario,
        )
        self._cambio_precio_proximo_mes()
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)), "al_dia"
        )

    def test_parcial_usa_precio_del_mes_no_el_futuro(self):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        self._cambio_precio_proximo_mes(50000)
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)),
            "deuda_parcial",
        )
        pagado, precio = montos_del_mes(self.cliente, date(2026, 4, 15))
        self.assertEqual((pagado, precio - pagado), (20000, 15000))

    def test_segunda_edicion_mismo_mes_gana_la_ultima(self):
        self._cambio_precio_proximo_mes(40000)
        PlanPrecio.objects.update_or_create(
            plan=self.plan,
            vigencia_desde=date(2026, 5, 1),
            defaults={"precio": 45000},
        )
        self.assertEqual(montos_del_mes(self.cliente, date(2026, 5, 15)), (0, 45000))


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class PlanesViewsTestCase(BaseTestCase):
    """Gestión de planes desde la app — solo dueño."""

    def setUp(self):
        super().setUp()
        self.dueno = User.objects.create_user(
            username="dueno", password="dueno123", rol="dueño"
        )

    def test_profesor_no_puede_ver_planes(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.get("/planes/")
        self.assertEqual(response.status_code, 403)

    def test_dueno_puede_ver_planes(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/planes/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.plan.nombre)
        self.assertContains(response, "Nuevo Plan")

    def test_dueno_edita_precio_crea_vigencia_proximo_mes(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.post(
            f"/plan/{self.plan.id}/editar/",
            {"nombre": self.plan.nombre, "precio": "40000", "activo": "on"},
        )
        self.assertEqual(response.status_code, 204)
        filas = PlanPrecio.objects.filter(plan=self.plan, precio=40000)
        self.assertEqual(filas.count(), 1)
        self.assertGreater(filas.first().vigencia_desde, date.today().replace(day=1))

    def test_profesor_no_edita_plan(self):
        self.client.login(username="testuser", password="test123")
        response = self.client.post(
            f"/plan/{self.plan.id}/editar/",
            {"nombre": self.plan.nombre, "precio": "40000", "activo": "on"},
        )
        self.assertEqual(response.status_code, 403)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.precio, 35000)

    def test_dueno_crea_plan_con_precio_inicial(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.post(
            "/plan/crear/",
            {"codigo": "libre", "nombre": "Libre", "precio": "55000", "activo": "on"},
        )
        self.assertEqual(response.status_code, 204)
        plan = Plan.objects.get(codigo="libre")
        self.assertEqual(plan.precio, 55000)
        fila = plan.precios.first()
        self.assertIsNotNone(fila)
        self.assertEqual(fila.precio, 55000)
        self.assertEqual(fila.vigencia_desde, date.today().replace(day=1))

    def test_planes_muestra_precio_pendiente(self):
        PlanPrecio.objects.create(
            plan=self.plan, precio=40000, vigencia_desde=date(2026, 10, 1)
        )
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/planes/")
        self.assertContains(response, "40000")


@override_settings(
    DEBUG=True,
    AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"],
)
class ModalPagoPrecioVigenteTestCase(BaseTestCase):
    """El modal de pago sugiere el precio vigente del mes, no un futuro pendiente."""

    def test_sugiere_precio_vigente_con_cambio_pendiente(self):
        PlanPrecio.objects.create(
            plan=self.plan, precio=40000, vigencia_desde=date(2026, 5, 1)
        )
        self.client.login(username="testuser", password="test123")
        with patch.dict(os.environ, {"FAKE_TODAY": "2026-04-15"}):
            response = self.client.get(f"/pagos/pago/{self.cliente.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["precio_mes"], 35000)
        self.assertNotContains(response, "40000")


class PagoParcialEstadoTestCase(BaseTestCase):
    """Tests del estado con pagos parciales acumulados por mes"""

    def _crear_pago(self, monto, mes, dia=15):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, dia),
            mes_cubierto=mes,
            monto=monto,
            usuario_registrador=self.usuario,
        )

    def test_dos_pagos_suman_y_completan_mes(self):
        self._crear_pago(20000, date(2026, 4, 1))
        self._crear_pago(15000, date(2026, 4, 1))
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)), "al_dia"
        )
        self.assertEqual(
            montos_del_mes(self.cliente, date(2026, 4, 15)), (35000, 35000)
        )

    def test_parcial_despues_del_10_deuda_parcial(self):
        self._crear_pago(20000, date(2026, 4, 1))
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)),
            "deuda_parcial",
        )
        pagado, precio = montos_del_mes(self.cliente, date(2026, 4, 15))
        self.assertEqual((pagado, precio - pagado), (20000, 15000))

    def test_parcial_antes_del_10_al_dia(self):
        self._crear_pago(20000, date(2026, 4, 1), dia=8)
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 8)), "al_dia"
        )

    def test_pago_exacto_del_plan_al_dia(self):
        self._crear_pago(35000, date(2026, 4, 1))
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)), "al_dia"
        )

    def test_sin_pago_despues_del_10_vencido(self):
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)), "vencido"
        )


@override_settings(DEBUG=True)
class FakeTodayTestCase(BaseTestCase):
    """FAKE_TODAY (solo DEBUG) permite simular la fecha en desarrollo"""

    def test_fake_today_simula_vencido(self):
        with patch.dict(os.environ, {"FAKE_TODAY": "2026-09-15"}):
            self.assertEqual(calcular_estado_cliente(self.cliente), "vencido")

    def test_fake_today_parcial(self):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 9, 12),
            mes_cubierto=date(2026, 9, 1),
            monto=15000,
            usuario_registrador=self.usuario,
        )
        with patch.dict(os.environ, {"FAKE_TODAY": "2026-09-15"}):
            self.assertEqual(calcular_estado_cliente(self.cliente), "deuda_parcial")
            self.assertEqual(montos_del_mes(self.cliente), (15000, 35000))


@override_settings(DEBUG=True)
class FakeTodayNoEnvTestCase(BaseTestCase):
    """Sin FAKE_TODAY usa la fecha real del sistema"""

    def test_sin_env_usar_fecha_real(self):
        self.assertEqual(
            calcular_estado_cliente(self.cliente, date(2026, 4, 15)), "vencido"
        )


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class RegistroPagoParcialViewTestCase(BaseTestCase):
    """El formulario y la vista permiten varios pagos por mes"""

    def test_form_segundo_pago_mismo_mes_valido(self):
        from apps.pagos.forms import PagoEditarForm

        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 15),
            mes_cubierto=date(2026, 4, 1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        instancia = Pago(cliente=self.cliente, usuario_registrador=self.usuario)
        form = PagoEditarForm(
            data={
                "mes_cubierto": "2026-04",
                "monto": "15000",
                "observaciones": "",
            },
            instance=instancia,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_post_segundo_pago_mismo_mes_204(self):
        from django.test import Client

        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date.today(),
            mes_cubierto=date.today().replace(day=1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        c = Client()
        c.login(username="testuser", password="test123")
        response = c.post(
            f"/pagos/pago/{self.cliente.id}/",
            {
                "mes_cubierto": date.today().strftime("%Y-%m"),
                "monto": "15000",
                "observaciones": "",
            },
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            Pago.objects.filter(
                cliente=self.cliente, mes_cubierto=date.today().replace(day=1)
            ).count(),
            2,
        )

    def test_get_modal_prefill_resta_cuando_parcial(self):
        Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date.today(),
            mes_cubierto=date.today().replace(day=1),
            monto=20000,
            usuario_registrador=self.usuario,
        )
        self.client.login(username="testuser", password="test123")
        response = self.client.get(f"/pagos/pago/{self.cliente.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["resumen_mes"]["restante"], 15000)
        self.assertEqual(
            response.context["form"].initial["monto"], 15000
        )


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class ImportarXmlTestCase(BaseTestCase):
    """Tests funcionales de importar_xml"""

    def setUp(self):
        super().setUp()
        self.dueno = User.objects.create_user(
            username="dueno", password="dueno123", rol="dueño"
        )
        self.client.login(username="dueno", password="dueno123")

    def _post_xml(self, xml_bytes):
        archivo = SimpleUploadedFile("backup.xml", xml_bytes, content_type="text/xml")
        return self.client.post("/importar/xml/", {"archivo": archivo})

    def test_importa_cliente_y_pago_nuevos(self):
        xml = """<gimnasio>
<clientes>
  <cliente><id>1</id><nombre>Ana</nombre><apellido>Garcia</apellido>
    <telefono>123</telefono><email>ana@test.com</email>
    <plan>3_dias</plan><turno>Mañana</turno><activo>True</activo></cliente>
</clientes>
<pagos>
  <pago><id>1</id><cliente_id>1</cliente_id><fecha_pago>2026-04-01</fecha_pago>
    <mes_cubierto>2026-04-01</mes_cubierto><monto>35000</monto>
    <observaciones></observaciones></pago>
</pagos>
</gimnasio>""".encode("utf-8")
        response = self._post_xml(xml)
        self.assertEqual(response.status_code, 200)
        resultado = response.context["resultado"]
        self.assertEqual(resultado["clientes_creados"], 1)
        self.assertEqual(resultado["pagos_creados"], 1)
        self.assertEqual(resultado["pagos_saltados"], 0)
        self.assertTrue(
            Pago.objects.filter(
                cliente__apellido="Garcia",
                mes_cubierto=date(2026, 4, 1),
                monto=35000,
            ).exists()
        )

    def test_pago_duplicado_dentro_del_mismo_archivo_se_salta(self):
        xml = """<gimnasio>
<clientes>
  <cliente><id>1</id><nombre>Ana</nombre><apellido>Garcia</apellido>
    <telefono>123</telefono><email>ana@test.com</email>
    <plan>3_dias</plan><turno>Mañana</turno><activo>True</activo></cliente>
</clientes>
<pagos>
  <pago><id>1</id><cliente_id>1</cliente_id><fecha_pago>2026-04-01</fecha_pago>
    <mes_cubierto>2026-04-01</mes_cubierto><monto>35000</monto>
    <observaciones></observaciones></pago>
  <pago><id>2</id><cliente_id>1</cliente_id><fecha_pago>2026-04-01</fecha_pago>
    <mes_cubierto>2026-04-01</mes_cubierto><monto>35000</monto>
    <observaciones></observaciones></pago>
</pagos>
</gimnasio>""".encode("utf-8")
        response = self._post_xml(xml)
        self.assertEqual(response.status_code, 200)
        resultado = response.context["resultado"]
        self.assertEqual(resultado["clientes_creados"], 1)
        self.assertEqual(resultado["pagos_creados"], 1)
        self.assertEqual(resultado["pagos_saltados"], 1)
