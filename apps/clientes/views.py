from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cliente
from apps.clientes.services import obtener_turno_actual, calcular_estado_cliente
from django.db.models import Q
from .forms import ClienteForm
from django.http import HttpResponse


@login_required
def dashboard(request):
    """
    Vista principal del dashboard.
    Si es request HTMX, devuelve solo el partial.
    Si es request normal, devuelve página completa.
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

    # Obtener parámetros de búsqueda y filtro
    busqueda = request.GET.get("busqueda", "").strip()
    filtro_estado = request.GET.get("estado", "")

    # Query base: clientes del turno actual
    clientes_qs = Cliente.objects.filter(activo=True)

    # Filtrar por turno
    if turno_actual:
        clientes_qs = clientes_qs.filter(turno=turno_actual)

    # Aplicar búsqueda (nombre O apellido)
    if busqueda:
        clientes_qs = clientes_qs.filter(
            Q(nombre__icontains=busqueda) | Q(apellido__icontains=busqueda)
        )

    # Optimización: traer relaciones en una query
    clientes_qs = clientes_qs.select_related("turno", "usuario_creador")

    # Calcular estado y aplicar filtro de estado
    clientes = []
    for cliente in clientes_qs:
        cliente.estado_actual = calcular_estado_cliente(cliente)

        # Filtrar por estado si se seleccionó uno
        if filtro_estado:
            if filtro_estado == "al_dia" and cliente.estado_actual != "al_dia":
                continue
            elif filtro_estado == "vencido" and cliente.estado_actual != "vencido":
                continue
            elif (
                filtro_estado == "pendiente"
                and cliente.estado_actual != "pendiente_consulta"
            ):
                continue

        clientes.append(cliente)

    context = {
        "turnos": turnos,
        "turno_actual": turno_actual,
        "clientes": clientes,
        "busqueda": busqueda,
        "filtro_estado": filtro_estado,
    }

    # Si es request HTMX, devolver solo el partial
    if request.headers.get("HX-Request"):
        return render(request, "clientes/_tabla_clientes.html", context)

    # Si es request normal, devolver página completa
    return render(request, "clientes/dashboard.html", context)


@login_required
def modal_historial_pagos(request, cliente_id):
    """
    Muestra el historial de pagos de un cliente.
    """
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtener pagos ordenados por más reciente
    pagos = cliente.pagos.all().order_by("-fecha_pago")

    context = {
        "cliente": cliente,
        "pagos": pagos,
    }

    return render(request, "clientes/_modal_historial.html", context)


@login_required
def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario_creador = request.user
            cliente.save()
            return HttpResponse(
                status=204, headers={"HX-Trigger": "clienteActualizado"}
            )
    else:
        form = ClienteForm()
    return render(request, "clientes/_modal_cliente.html", {"form": form})


@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return HttpResponse(
                status=204, headers={"HX-Trigger": "clienteActualizado"}
            )
    else:
        form = ClienteForm(instance=cliente)
    return render(
        request, "clientes/_modal_cliente.html", {"form": form, "cliente": cliente}
    )
