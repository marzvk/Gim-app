# Fase 2 — Decorator `@rol_requerido`

**Fecha:** 2026-04-18
**Problema:** La autorización estaba dispersa en 8 checks inline (`if request.user.rol != "dueño": return HttpResponseForbidden()`) copypasteados en cada vista. Fácil de olvidar al agregar endpoints nuevos. Además, borrar pagos no tenía restricción de rol — cualquier profesor podía borrar.

## Solución

### 1. Decorator `rol_requerido` (apps/usuarios/decorators.py)

```python
def rol_requerido(rol_permitido):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.rol != rol_permitido:
                return HttpResponseForbidden("No tenés permiso para acceder a esta página.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
```

Reemplaza `@login_required` + check inline en una sola línea: `@rol_requerido("dueño")`.

### 2. Views actualizadas

**clientes/views.py** — 8 checks reemplazados:

| Vista | Antes | Ahora |
|---|---|---|
| `confirmar_inactivar_cliente` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `reportes` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `exportar_xml` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `importar_xml` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `exportar_excel` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `importar_excel` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `exportar_csv` | `@login_required` + if/403 | `@rol_requerido("dueño")` |
| `importar_csv` | `@login_required` + if/403 | `@rol_requerido("dueño")` |

**pagos/views.py** — 2 endpoints nuevos protegidos:

| Vista | Antes | Ahora |
|---|---|---|
| `borrar_pago` | `@login_required` (cualquiera) | `@rol_requerido("dueño")` |
| `confirmar_borrar_pago` | `@login_required` (cualquiera) | `@rol_requerido("dueño")` |

### 3. Fix de test existente + test nuevo

- `BorrarPagoViewTestCase` ahora usa usuario `dueno` (rol="dueño") para los tests de borrar
- Nuevo test: `test_profesor_no_puede_borrar_pago` — verifica que un profesor recibe 403

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `apps/usuarios/decorators.py` | **Nuevo** — decorator `rol_requerido` |
| `apps/clientes/views.py` | 8 checks inline → 8 decoradores |
| `apps/pagos/views.py` | `borrar_pago` + `confirmar_borrar_pago` → `@rol_requerido("dueño")` |
| `apps/pagos/tests.py` | Fix setUp borrar + test nuevo 403 |

## Resultado

- **39 tests** (38 + 1 nuevo), todos pasan
- Un solo lugar para la lógica de autorización por rol
- Borrar pagos ahora es operación de dueño solamente
- Cero `HttpResponseForbidden` sueltos en views
