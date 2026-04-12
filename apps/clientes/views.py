from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Cliente
from apps.clientes.services import obtener_turno_actual, calcular_estado_cliente


@login_required
def dashboard(request):
    """
    Vista principal del dashboard.
    Muestra clientes filtrados por turno.
    """
    # Obtener todos los turnos activos
    from apps.usuarios.models import Turno

    turnos = Turno.objects.filter(activo=True).order_by("hora_inicio")

    # Determinar qué turno mostrar
    turno_seleccionado_id = request.GET.get("turno")

    if turno_seleccionado_id:
        # Usuario seleccionó un turno manualmente
        turno_actual = Turno.objects.filter(
            id=turno_seleccionado_id, activo=True
        ).first()
    else:
        # Detectar turno automáticamente según la hora
        turno_actual = obtener_turno_actual()

    # Obtener clientes del turno actual
    clientes = []
    if turno_actual:
        clientes_qs = Cliente.objects.filter(
            turno=turno_actual, activo=True
        ).select_related("turno", "usuario_creador")

        # Calcular estado de cada cliente
        for cliente in clientes_qs:
            cliente.estado_actual = calcular_estado_cliente(cliente)
            clientes.append(cliente)

    context = {
        "turnos": turnos,
        "turno_actual": turno_actual,
        "clientes": clientes,
    }
    return render(request, "clientes/dashboard.html", context)
