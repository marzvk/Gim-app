# Fase 3 — Tests de autorización

**Fecha:** 2026-04-18
**Problema:** `apps/usuarios/tests.py` estaba vacío. Sin cobertura de autorización, un cambio accidental podría abrir endpoints protegidos sin que nadie lo note.

## Solución: Suite de tests de autorización

15 tests nuevos en `apps/usuarios/tests.py` organizados en 5 clases:

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

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `apps/usuarios/tests.py` | De 3 líneas a 178 — suite completa de autorización |

## Resultado

- **54 tests** (39 + 15 nuevos), todos pasan
- Cobertura de autorización: cada endpoint protegido tiene al menos 1 test de 403
- Tests positivos:dueño puede acceder a todo lo que le corresponde
- Tests de usuarios abiertos: profesor puede acceder a las vistas que le corresponden
