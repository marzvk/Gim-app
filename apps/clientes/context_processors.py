from apps.clientes.services import clientes_no_al_dia


def notificaciones(request):
    """
    Pone en el contexto la cantidad de clientes que no completaron el mes
    (vencidos + parciales) para el badge del navbar.
    Para usuarios no autenticados devuelve 0 (no hay navbar).
    """

    if not request.user.is_authenticated:
        return {"cantidad_no_al_dia": 0}

    return {"cantidad_no_al_dia": len(clientes_no_al_dia(request.user))}