from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date
from django.http import HttpResponse

from apps.clientes.models import Cliente
from .models import Pago
from .forms import PagoEditarForm


@login_required
def modal_registrar_pago(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == "POST":
        pago_instancia = Pago(cliente=cliente, usuario_registrador=request.user)
        form = PagoEditarForm(data=request.POST, instance=pago_instancia)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.fecha_pago = date.today()
            pago.save()

            # Si el cliente estaba inactivo, reactivarlo
            if not cliente.activo:
                cliente.activo = True
                cliente.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "pagoActualizado"})
    else:
        mes_inicial = date.today().replace(day=1).strftime("%Y-%m")
        monto_inicial = cliente.plan.precio if cliente.plan else 0
        form = PagoEditarForm(
            initial={"mes_cubierto": mes_inicial, "monto": monto_inicial}
        )

    return render(request, "pagos/_modal_pago.html", {"cliente": cliente, "form": form})


@login_required
def editar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    cliente = pago.cliente

    if request.method == "POST":
        form = PagoEditarForm(data=request.POST, instance=pago)
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
    pago = get_object_or_404(Pago, id=pago_id)
    cliente = pago.cliente

    if request.method == "POST":
        pago.delete()
        pagos = Pago.objects.filter(cliente=cliente).order_by("-fecha_pago")
        response = render(
            request,
            "clientes/_modal_historial.html",
            {"cliente": cliente, "pagos": pagos},
        )
        response["HX-Trigger"] = "pagoActualizado"
        return response
    return HttpResponse(status=405)


@login_required
def confirmar_borrar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    return render(request, "pagos/_modal_confirmar_borrado.html", {"pago": pago})
