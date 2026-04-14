from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from django.http import HttpResponse

from apps.clientes.models import Cliente
from .models import Pago
from .forms import PagoEditarForm


@login_required
def modal_registrar_pago(request, cliente_id):
    """Modal de pago del cliente.
    Si es POST, guarda el pago."""

    cliente = get_object_or_404(Cliente, id=cliente_id, activo=True)

    if request.method == "POST":
        monto = request.POST.get("monto")
        fecha_pago = request.POST.get("fecha_pago") or date.today()
        observaciones = request.POST.get("observaciones", "")

        if not monto:
            messages.error(request, "El monto es obligatorio")
        else:
            try:
                monto = float(monto)

                mes_cubierto = date.today().replace(day=1)

                Pago.objects.create(
                    cliente=cliente,
                    fecha_pago=fecha_pago,
                    mes_cubierto=mes_cubierto,
                    monto=monto,
                    observaciones=observaciones,
                    usuario_registrador=request.user,
                )
                messages.success(
                    request, f"Pago registrado para {cliente.nombre} {cliente.apellido}"
                )

                return render(request, "pagos/_pago_success.html")

            except ValueError:
                messages.error(request, "Monto invalido")

    ctx = {"cliente": cliente, "today": date.today()}

    return render(request, "pagos/_modal_pago.html", ctx)


@login_required
def editar_pago(request, pago_id):
    """Muestra el modal para editar un pago existente."""
    pago = get_object_or_404(Pago, id=pago_id)
    cliente = pago.cliente

    if request.method == "POST":
        form = PagoEditarForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            pagos = Pago.objects.filter(cliente=cliente).order_by("-fecha_pago")
            return render(
                request,
                "clientes/_modal_historial.html",
                {"cliente": cliente, "pagos": pagos},
            )
    else:
        form = PagoEditarForm(instance=pago)
    return render(
        request, "pagos/_modal_editar_pago.html", {"form": form, "pago": pago}
    )


@login_required
def borrar_pago(request, pago_id):
    """Borra un pago y notifica a HTMX para refrescar la lista."""
    pago = get_object_or_404(Pago, id=pago_id)
    cliente = pago.cliente

    if request.method == "POST":
        pago.delete()

        # OBTENEMOS EL HISTORIAL ACTUALIZADO
        pagos = Pago.objects.filter(cliente=cliente).order_by("-fecha_pago")

        return render(
            request,
            "clientes/_modal_historial.html",
            {"cliente": cliente, "pagos": pagos},
        )
    return HttpResponse(status=405)


@login_required
def confirmar_borrar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    return render(request, "pagos/_modal_confirmar_borrado.html", {"pago": pago})
