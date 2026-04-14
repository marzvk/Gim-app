from django import template

register = template.Library()


@register.filter
def sum_monto(pagos):
    """Suma total de montos de una lista de pagos"""
    return sum(pago.monto for pago in pagos)
