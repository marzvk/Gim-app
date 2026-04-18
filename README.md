# 🏋️ GimApp — Sistema de Gestión para Gimnasios

Sistema web para la gestión de clientes, pagos y reportes de gimnasios. Desarrollado con Django, HTMX y Bootstrap 5.

---

## ¿Qué hace?

### Gestión de Clientes
- Alta, edición e inactivación de clientes
- Asignación de plan y turno por cliente
- Búsqueda por nombre o apellido en tiempo real
- Filtro por estado de pago
- Los clientes inactivos aparecen solo al buscar por nombre (no saturan la tabla)
- Reactivación automática al registrar un nuevo pago

### Gestión de Pagos
- Registro de pagos por cliente con mes cubierto y monto
- Edición y borrado de pagos
- Historial completo de pagos por cliente
- Validación: no permite registrar dos pagos para el mismo mes
- Monto sugerido según el plan del cliente

### Estados de Clientes (automáticos)
- ✅ **Al día** — pagó el mes actual, o estamos antes del día 10
- ❌ **Vencido** — pasó el día 10 sin pago del mes
- ⚠️ **Pendiente consulta** — 2 meses sin pagar desde el vencimiento
- 🚫 **Inactivo** — dado de baja manualmente por el dueño

### Turnos
- Mañana, Tarde y Noche
- Detección automática del turno según la hora actual
- Dashboard organizado por tabs de turno

### Reportes (solo dueño)
- Métricas por turno: total de clientes, al día, vencidos, pendientes
- Porcentaje de vencidos por turno
- Ingresos del mes por turno

### Backup de Datos
- Exportar clientes y pagos en **XML**, **Excel** o **CSV**
- Importar desde cualquiera de esos formatos
- Lógica de importación inteligente: no duplica clientes ni pagos existentes
- Compatible con migración de base de datos

### Usuarios y Roles
- **Profesor** — gestiona clientes y pagos de su turno
- **Dueño** — acceso completo + reportes + backup + inactivar clientes
- Login/logout con redirección automática

### UX
- Interfaz 100% sin recargas de página (HTMX)
- Notificaciones tipo Toast para confirmaciones
- Spinner de carga en requests
- Dark mode toggle
- Responsive para tablet y desktop

---

## Stack Técnico

| Componente | Tecnología |
|---|---|
| Backend | Django 6.0.4 + Python 3.12 |
| Frontend | Bootstrap 5.3 + HTMX 1.9.10 |
| Base de datos | SQLite (producción actual) |
| Exportación | openpyxl (Excel), xml.etree, csv |
| Autenticación | Django Auth + AbstractUser |
| Deploy | PythonAnywhere |

---

## Arquitectura

```
apps/
  clientes/   — modelos Cliente y Plan, vistas, servicios, formularios
  pagos/      — modelo Pago, vistas, formularios, templatetags
  usuarios/   — modelo Usuario (AbstractUser) y Turno
config/       — settings, urls, wsgi
templates/    — base.html + partials por app
static/       — CSS y JS propios
```

### Decisiones técnicas relevantes

**Modal Shell estático**
Un único `<div class="modal">` vive siempre en el DOM. HTMX reemplaza solo el contenido interno (`modal-content`). Evita conflictos de backdrop y errores de foco de Bootstrap al navegar entre modales.

**Búsqueda con HTMX**
La búsqueda dispara requests con delay de 300ms. Cuando hay texto activo, ignora el filtro de turno y busca en todos (incluyendo inactivos). Cuando no hay texto, filtra por turno actual.

**Estados calculados en tiempo real**
`calcular_estado_cliente()` se ejecuta en cada request, sin campo persistente. Garantiza que el estado siempre refleja la fecha actual sin necesidad de tareas programadas.

**Importación con mapa de IDs**
Al importar, se construye un mapa `id_archivo → cliente_en_bd` para mantener la relación cliente-pago aunque los IDs cambien en la base de datos destino.

**Roles con Signal**
Cuando un usuario tiene `rol="dueño"`, un signal de Django le asigna automáticamente el grupo "Dueño" y activa `is_staff=True`.

---

## Tests

```bash
python manage.py test
```

Cubren: estados de clientes, lógica de pagos, validaciones de formularios, permisos por rol, vistas principales.

---

## Roadmap

- [ ] Reportes por mes con navegación histórica
- [ ] Panel propio para el dueño (sin Django admin)
- [ ] Migración a PostgreSQL
- [ ] Notificaciones de pagos vencidos
- [ ] App mobile