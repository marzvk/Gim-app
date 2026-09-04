from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from datetime import date

from apps.usuarios.models import Turno
from apps.clientes.models import Cliente, Plan
from apps.pagos.models import Pago

User = get_user_model()


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class BaseTestCase(TestCase):

    def setUp(self):
        self.turno = Turno.objects.create(
            nombre="Mañana", hora_inicio="07:30", hora_fin="11:00", activo=True
        )
        self.profesor = User.objects.create_user(
            username="profesor", password="profesor123", rol="profesor"
        )
        self.dueno = User.objects.create_user(
            username="dueno", password="dueno123", rol="dueño"
        )
        self.plan = Plan.objects.create(
            codigo="3_dias", nombre="3 veces por semana", precio=35000, activo=True
        )
        self.cliente = Cliente.objects.create(
            nombre="Juan",
            apellido="Pérez",
            plan=self.plan,
            turno=self.turno,
            activo=True,
            usuario_creador=self.dueno,
        )
        self.pago = Pago.objects.create(
            cliente=self.cliente,
            fecha_pago=date(2026, 4, 1),
            mes_cubierto=date(2026, 4, 1),
            monto=35000,
            usuario_registrador=self.dueno,
        )


class DecoradorRolRequeridoTestCase(BaseTestCase):
    """Tests del decorator @rol_requerido"""

    def test_no_autenticado_redirige_a_login(self):
        response = self.client.get("/reportes/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_profesor_no_puede_ver_reportes(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get("/reportes/")
        self.assertEqual(response.status_code, 403)

    def test_dueno_puede_ver_reportes(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/reportes/")
        self.assertEqual(response.status_code, 200)


class ExportImportAuthTestCase(BaseTestCase):
    """Tests de autorización en endpoints de exportar/importar"""

    def setUp(self):
        super().setUp()
        self.endpoints_dueno = [
            "/exportar/xml/",
            "/importar/xml/",
            "/exportar/excel/",
            "/importar/excel/",
            "/exportar/csv/",
            "/importar/csv/",
        ]

    def test_profesor_no_puede_exportar_ni_importar(self):
        self.client.login(username="profesor", password="profesor123")
        for url in self.endpoints_dueno:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 403, f"Profesor pudo acceder a {url}"
            )

    def test_dueno_puede_exportar(self):
        self.client.login(username="dueno", password="dueno123")
        for url in ["/exportar/xml/", "/exportar/excel/", "/exportar/csv/"]:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"Dueño no pudo acceder a {url}"
            )

    def test_dueno_puede_ver_formulario_importar(self):
        self.client.login(username="dueno", password="dueno123")
        for url in ["/importar/xml/", "/importar/excel/", "/importar/csv/"]:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"Dueño no pudo acceder a {url}"
            )


class InactivarClienteAuthTestCase(BaseTestCase):
    """Tests de autorización para inactivar cliente"""

    def test_profesor_no_puede_inactivar_cliente(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get(
            f"/cliente/{self.cliente.id}/inactivar/"
        )
        self.assertEqual(response.status_code, 403)

    def test_dueno_puede_inactivar_cliente(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get(
            f"/cliente/{self.cliente.id}/inactivar/"
        )
        self.assertEqual(response.status_code, 200)


class BorrarPagoAuthTestCase(BaseTestCase):
    """Tests de autorización para borrar pago"""

    def test_profesor_no_puede_borrar_pago(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.post(f"/pagos/borrar/{self.pago.id}/")
        self.assertEqual(response.status_code, 403)

    def test_profesor_no_puede_ver_confirmar_borrar(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get(
            f"/pagos/confirmar-borrar/{self.pago.id}/"
        )
        self.assertEqual(response.status_code, 403)

    def test_dueno_puede_borrar_pago(self):
        self.client.login(username="dueno", password="dueno123")
        response = self.client.post(f"/pagos/borrar/{self.pago.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Pago.objects.filter(id=self.pago.id).exists())


class ViewsAbiertasTestCase(BaseTestCase):
    """Tests que profesor SÍ puede acceder a estas vistas"""

    def test_profesor_puede_ver_dashboard(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_profesor_puede_crear_cliente(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get("/crear/")
        self.assertEqual(response.status_code, 200)

    def test_profesor_puede_registrar_pago(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get(f"/pagos/pago/{self.cliente.id}/")
        self.assertEqual(response.status_code, 200)

    def test_profesor_puede_editar_pago(self):
        self.client.login(username="profesor", password="profesor123")
        response = self.client.get(f"/pagos/editar/{self.pago.id}/")
        self.assertEqual(response.status_code, 200)


class SecurityTestCase(BaseTestCase):
    """Tests de seguridad: headers, rate limiting, validación uploads"""

    def test_headers_seguridad_presentes(self):
        """Verifica headers de seguridad en respuesta"""
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/reportes/")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("strict-origin-when-cross-origin", response["Referrer-Policy"])

    def test_upload_extension_invalida(self):
        """Rechaza archivos con extensión no permitida"""
        self.client.login(username="dueno", password="dueno123")
        from django.core.files.uploadedfile import SimpleUploadedFile
        archivo = SimpleUploadedFile("malicioso.txt", b"contenido", content_type="text/plain")
        response = self.client.post("/importar/xml/", {"archivo": archivo})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Extensión", response.content.decode())

    def test_upload_tamano_excede(self):
        """Rechaza archivos mayores a 2MB"""
        self.client.login(username="dueno", password="dueno123")
        from django.core.files.uploadedfile import SimpleUploadedFile
        contenido = b"x" * (3 * 1024 * 1024)
        archivo = SimpleUploadedFile("grande.xml", contenido, content_type="application/xml")
        response = self.client.post("/importar/xml/", {"archivo": archivo})
        self.assertEqual(response.status_code, 200)
        self.assertIn("2MB", response.content.decode())

    def test_login_lockout(self):
        """Bloquea tras 5 intentos fallidos (axes)"""
        from django.core.cache import cache
        cache.clear()
        for _ in range(6):
            self.client.post("/login/", {"username": "inexistente", "password": "wrong"})
        response = self.client.post("/login/", {"username": "inexistente", "password": "wrong"})
        self.assertEqual(response.status_code, 429)
        self.assertIn("bloqueado", response.content.decode())

    def test_xml_malicioso_xxe_rechazado(self):
        """Rechaza XML con entidad externa (XXE)"""
        self.client.login(username="dueno", password="dueno123")
        from django.core.files.uploadedfile import SimpleUploadedFile
        xxe_payload = (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            b'<gimnasio><clientes><cliente><id>1</id><nombre>Test</nombre>'
            b'<apellido>User</apellido><plan>3_dias</plan><turno>Manana</turno>'
            b'<activo>True</activo></cliente></clientes></gimnasio>'
        )
        archivo = SimpleUploadedFile("xxe.xml", xxe_payload, content_type="application/xml")
        response = self.client.post("/importar/xml/", {"archivo": archivo})
        self.assertEqual(response.status_code, 200)
        self.assertIn("entidades externas", response.content.decode())

    def test_proxy_ssl_header(self):
        """Verifica que SECURE_PROXY_SSL_HEADER funciona"""
        self.client.login(username="dueno", password="dueno123")
        response = self.client.get("/reportes/", HTTP_X_FORWARDED_PROTO="https")
        self.assertTrue(response.wsgi_request.is_secure())
