from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date

from apps.clientes.models import Cliente
from .models import Pago


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

        ctx = {
            "cliente": cliente,
        }

        return render(request, "pagos/_modal_pago.html", ctx)
