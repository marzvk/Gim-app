from django.db import models
from django.conf import settings


class Pago(models.Model):
    """Modelo de registro de los pagos mensuales.
    Cada pago es UN mes calendario."""

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="pagos"
    )

    fecha_pago = models.DateField(help_text="Fecha registro del pago")

    mes_cubierto = models.DateField(
        help_text="Mes que cubre el pago(se guarda como dia 1 del mes)"
    )

    monto = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Monto cobrado"
    )

    observaciones = models.TextField(
        blank=True,
        help_text="Notas adicionales(ej:"
        '"pago proporcional 9 dias", '
        '"pago por 2 dias esta semana")',
    )

    usuario_registrador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pagos_registrados",
        help_text="Usuario que registro este pago",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp del registro"
    )

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_pago"]

    def __str__(self):
        return f"{self.cliente} - {self.mes_cubierto.strftime('%m/%Y')} - ${self.monto}"
