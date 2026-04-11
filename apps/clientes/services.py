from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Max


def calcular_estado_cliente(cliente, fecha_hoy=None):

    if fecha_hoy is None:
        fecha_hoy = date.today()

    if not cliente.activo:
        return "inactivo"

    mes_actual = fecha_hoy.replace(day=1)

    tiene_pago_mes_actual = cliente.pagos.filter(mes_cubierto=mes_actual).exists()

    if tiene_pago_mes_actual or fecha_hoy.day <= 10:
        return "al_dia"

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

    # Si no encontró ninguno, devolver el último turno activo (caso borde)
    return turnos.last() if turnos.exists() else None
