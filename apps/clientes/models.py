from django.db import models
from django.conf import settings


class Cliente(models.Model):
    """Clientes del gim, tienen turno y plan."""

    PLAN_CHOICES = [
        ("3_dias", "3 días por semana"),
        ("5_dias", "5 días por semana"),
    ]

    ESTADO_CONSULTA_CHOICES = [
        ("ninguno", "Ninguno"),
        ("pendiente", "Pendiente consulta"),
        ("decidido", "Decidido"),
    ]

    nombre = models.CharField(
        max_length=100,
    )
    apellido = models.CharField(
        max_length=100,
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        help_text="Plan mensual del cliente",
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        help_text="Telefono de contacto",
    )

    email = models.EmailField(blank=True)

    turno = models.ForeignKey(
        "usuarios.Turno",
        on_delete=models.SET_NULL,
        null=True,
        related_name="clientes",
        help_text="Turno al que va cliente",
    )

    fecha_alta = models.DateField(
        auto_now_add=True,
    )

    activo = models.BooleanField(default=True)

    # Inactividad auto
    estado_consulta = models.CharField(
        max_length=20,
        choices=ESTADO_CONSULTA_CHOICES,
        default="ninguno",
        help_text="Estado de consulta por inactividad",
    )

    fecha_ultima_consulta = models.DateField(
        null=True,
        blank=True,
    )

    # Auditoria
    usuario_creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="clientes_creados",
        help_text="Quien dio de alta al cliente",
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.get_plan_display()})"
