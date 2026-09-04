# Fase 4 — Tests de Autorización y Seguridad

**Fecha:** 2026-09-04
**Problema:** `apps/usuarios/tests.py` estaba vacío. Sin cobertura de autorización y seguridad, un cambio accidental podría abrir endpoints protegidos o debilitar validaciones sin que nadie lo note.

## Solución: Suite completa de tests de autorización y seguridad

16 tests en `apps/usuarios/tests.py` organizados en 6 clases:

### DecoradorRolRequeridoTestCase (3 tests)
| Test | Qué valida |
|---|---|
| `test_no_autenticado_redirige_a_login` | Sin sesión → 302 a `/login/` |
| `test_profesor_no_puede_ver_reportes` | Profesor → 403 en reportes |
| `test_dueno_puede_ver_reportes` | Dueño → 200 en reportes |

### ExportImportAuthTestCase (3 tests)
| Test | Qué valida |
|---|---|
| `test_profesor_no_puede_exportar_ni_importar` | Profesor → 403 en los 6 endpoints de export/import |
| `test_dueno_puede_exportar` | Dueño → 200 en los 3 endpoints de export |
| `test_dueno_puede_ver_formulario_importar` | Dueño → 200 en los 3 formularios de import |

### InactivarClienteAuthTestCase (2 tests)
| Test | Qué valida |
|---|---|
| `test_profesor_no_puede_inactivar_cliente` | Profesor → 403 |
| `test_dueno_puede_inactivar_cliente` | Dueño → 200 |

### BorrarPagoAuthTestCase (3 tests)
| Test | Qué valida |
|---|---|
| `test_profesor_no_puede_borrar_pago` | Profesor → 403 |
| `test_profesor_no_puede_ver_confirmar_borrar` | Profesor → 403 en confirmación |
| `test_dueno_puede_borrar_pago` | Dueño → 200, pago eliminado |

### ViewsAbiertasTestCase (4 tests)
| Test | Qué valida |
|---|---|
| `test_profesor_puede_ver_dashboard` | Profesor → 200 en `/` |
| `test_profesor_puede_crear_cliente` | Profesor → 200 en `/crear/` |
| `test_profesor_puede_registrar_pago` | Profesor → 200 en `/pagos/pago/` |
| `test_profesor_puede_editar_pago` | Profesor → 200 en `/pagos/editar/` |

### SecurityTestCase (6 tests)
| Test | Qué valida |
|---|---|
| `test_headers_seguridad_presentes` | X-Frame-Options=DENY, X-Content-Type-Options=nosniff, Referrer-Policy strict-origin-when-cross-origin |
| `test_upload_extension_invalida` | Rechaza .txt en import XML (200 + mensaje "Extensión") |
| `test_upload_tamano_excede` | Rechaza >2MB (200 + mensaje "2MB") |
| `test_login_lockout` | Axes bloquea tras 5 intentos fallidos → 429 + mensaje "bloqueado" |
| `test_xml_malicioso_xxe_rechazado` | defusedxml rechaza entidad externa XXE (200 + mensaje "entidades externas") |
| `test_proxy_ssl_header` | SECURE_PROXY_SSL_HEADER detecta HTTPS detrás de proxy (`is_secure()` = True) |

## Configuración clave para tests

`BaseTestCase` usa `@override_settings` para desactivar `AxesBackend` durante tests:

```python
@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class BaseTestCase(TestCase):
    ...
```

**Por qué:** `AxesBackend.authenticate()` requiere un objeto `request`, pero `client.login()` de Django test no lo pasa. Esto evita `AxesBackendRequestParameterRequired` en todos los tests que usan `client.login()`.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `apps/usuarios/tests.py` | De 3 líneas a 227 — suite completa de autorización y seguridad |

## Resultado

- **60 tests totales** (44 previos + 16 nuevos), todos pasan
- Cobertura de autorización: cada endpoint protegido tiene al menos 1 test de 403
- Tests positivos: dueño puede acceder a todo lo que le corresponde
- Tests de usuarios abiertos: profesor puede acceder a las vistas que le corresponden
- Cobertura de seguridad: headers, rate limiting (axes), validación uploads (extensión, tamaño, XXE), proxy SSL

## Referencias cruzadas

- `DEPLOY.md` → Sección 6 Troubleshooting: "Axes bloquea admin" (cambiar `AXES_ENABLE_ADMIN = False` en prod)
- `config/settings.py` → `AXES_ENABLE_ADMIN = False` antes de deploy