import os
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Max, Sum


def _fecha_hoy_dev():
    """
    Fecha usada como "hoy".
    Solo en desarrollo (DEBUG=True) se puede simular con la env FAKE_TODAY=YYYY-MM-DD
    para visualizar estados de vencimiento. En producción se ignora.
    """
    if settings.DEBUG:
        fake = os.environ.get("FAKE_TODAY", "")
        try:
            return date.fromisoformat(fake)
        except ValueError:
            pass
    return date.today()


def calcular_estado_cliente(cliente, fecha_hoy=None):
    """
    Estados:
      - inactivo: cliente desactivado manualmente.
      - al_dia: sumó lo del plan en el mes actual, o es antes/igual del día 10 (gracia).
      - deuda_parcial: pagó algo del mes pero menos que el precio del plan (después del 10).
      - vencido: no pagó nada del mes actual (después del 10).
      - pendiente_consulta: 2 meses desde el vencimiento, esperando decisión del dueño.
    """

    if fecha_hoy is None:
        fecha_hoy = _fecha_hoy_dev()

    if not cliente.activo:
        return "inactivo"

    pagado_mes, precio_plan = montos_del_mes(cliente, fecha_hoy)

    if pagado_mes >= precio_plan:
        return "al_dia"

    if fecha_hoy.day <= 10:
        return "al_dia"

    if pagado_mes > 0:
        return "deuda_parcial"

    ultimo_pago = cliente.pagos.order_by("-mes_cubierto").first()

    if ultimo_pago:
        # Mes que venció (mes siguiente al último pago)
        mes_vencido = ultimo_pago.mes_cubierto + relativedelta(months=1)
        # Fecha de vencimiento (día 10 de ese mes)
        fecha_vencimiento = mes_vencido.replace(day=10)
        # 2 meses después del vencimiento
        fecha_limite_inactividad = fecha_vencimiento + relativedelta(months=2)

        if fecha_hoy >= fecha_limite_inactividad:
            return "pendiente_consulta"

    return "vencido"


def montos_del_mes(cliente, fecha_hoy=None):
    """
    Devuelve (pagado, precio_plan) para el mes calendario de fecha_hoy.
    Permite varios pagos por mes: se acumulan en 'pagado'.
    """

    if fecha_hoy is None:
        fecha_hoy = _fecha_hoy_dev()

    mes = fecha_hoy.replace(day=1)
    pagado = (
        cliente.pagos.filter(mes_cubierto=mes).aggregate(total=Sum("monto"))["total"]
        or 0
    )
    precio = cliente.plan.precio if cliente.plan else 0

    return pagado, precio


#
def marcar_clientes_inactivos():

    from apps.clientes.models import Cliente

    fecha_hoy = date.today()
    clientes_activos = Cliente.objects.filter(activo=True, estado_consulta="ninguno")

    marcados = 0

    for cliente in clientes_activos:
        estado = calcular_estado_cliente(cliente, fecha_hoy)

        if estado == "pendiente_consulta":
            cliente.estado_consulta = "pendiente"
            cliente.fecha_ultima_consulta = fecha_hoy
            cliente.save(update_fields=["estado_consulta", "fecha_ultima_consulta"])
            marcados += 1

    return marcados


#
def obtener_turno_actual():

    from apps.usuarios.models import Turno
    from datetime import datetime

    hora_actual = datetime.now().time()

    # Buscar turno donde hora_actual esté entre hora_inicio y hora_fin
    turnos = Turno.objects.filter(activo=True).order_by("hora_inicio")

    for turno in turnos:
        # hora_inicio es inclusive, hora_fin es exclusive
        if turno.hora_inicio <= hora_actual < turno.hora_fin:
            return turno

    # Si no encontró , none
    return None


#
def clientes_no_al_dia(usuario):
    """
    Clientes activos que NO tienen completo el mes actual ('vencido' o 'deuda_parcial'),
    según el rol. Dueño: todos los turnos. Profesor: solo su turno_asignado.
    Adjunta estado_actual, mes_actual, pagado_mes_actual, precio_plan y monto_debido.
    """

    from apps.clientes.models import Cliente

    fecha_hoy = _fecha_hoy_dev()
    clientes_qs = Cliente.objects.filter(activo=True).select_related("turno", "plan")

    if usuario.rol == "profesor":
        if not usuario.turno_asignado:
            return []
        clientes_qs = clientes_qs.filter(turno=usuario.turno_asignado)

    resultado = []
    for cliente in clientes_qs:
        estado = calcular_estado_cliente(cliente, fecha_hoy)
        if estado not in ("vencido", "deuda_parcial"):
            continue

        pagado, precio = montos_del_mes(cliente, fecha_hoy)
        cliente.estado_actual = estado
        cliente.mes_actual = fecha_hoy.replace(day=1)
        cliente.pagado_mes_actual = pagado
        cliente.precio_plan = precio
        cliente.monto_debido = max(precio - pagado, 0)
        resultado.append(cliente)

    return resultado
