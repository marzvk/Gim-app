# Fase 1 — UniqueConstraint en Pago

**Fecha:** 2026-04-18
**Problema:** La prevención de pagos duplicados (cliente + mes) vivía solo en la capa de forms (`clean()`). Race conditions, bypass desde admin o ORM podían crear pagos duplicados.

## Solución: Triple capa de protección

### 1. `Pago.save()` — Normalización (apps/pagos/models.py)

```python
def save(self, *args, **kwargs):
    if self.mes_cubierto:
        self.mes_cubierto = self.mes_cubierto.replace(day=1)
    super().save(*args, **kwargs)
```

Siempre guarda `mes_cubierto` como día 1 del mes, sin importar qué valor llegue.

### 2. `UniqueConstraint` — Protección a nivel SQL (apps/pagos/models.py)

```python
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=["cliente", "mes_cubierto"],
            name="unique_pago_por_mes",
        )
    ]
```

El DB rechaza duplicados directamente. Sin race conditions posibles.

### 3. `IntegrityError` — Manejo graceful en vistas

- `apps/pagos/views.py`: `modal_registrar_pago` — envuelve `save()` en `try/except IntegrityError`, re-renderiza el form con error.
- `apps/clientes/views.py`: `importar_xml`, `importar_excel`, `importar_csv` — envuelven `Pago.objects.create()` en `try/except IntegrityError`, incrementan `pagos_saltados` y continúan.

### 4. `PagoAdmin` con form (apps/pagos/admin.py)

```python
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    form = PagoEditarForm
```

El admin ahora pasa por la misma validación de `clean()` que la vista.

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `apps/pagos/models.py` | `save()` normalizador + `UniqueConstraint` |
| `apps/pagos/views.py` | `IntegrityError` en `modal_registrar_pago` |
| `apps/pagos/admin.py` | `form = PagoEditarForm` |
| `apps/pagos/tests.py` | 4 tests nuevos |
| `apps/pagos/migrations/0002_pago_unique_pago_por_mes.py` | Migración generada |
| `apps/clientes/views.py` | `IntegrityError` en 3 vistas de import |

## Tests nuevos (4)

| Test | Qué valida |
|---|---|
| `test_save_normaliza_mes_cubierto_a_dia_1` | `Pago.save()` convierte día 15 → día 1 |
| `test_unique_constraint_previene_duplicado` | `IntegrityError` a nivel DB en pago duplicado |
| `test_clientes_distintos_pueden_pagar_mismo_mes` | Constraint solo aplica por cliente |
| `test_integrity_error_en_registrar_pago_view` | Vista devuelve 200 (form con error) en vez de 500 |

## Resultado

- **38 tests** (34 originales + 4 nuevos), todos pasan
- Migración aplicada a DB local
- Cero pagos duplicados posible desde cualquier capa (form, admin, ORM, importaciones)
