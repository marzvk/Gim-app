from django.db import models
from django.conf import settings


class Plan(models.Model):
    """
    Planes de entrenamiento disponibles en el gimnasio.
    El dueño puede configurarlos.
    """

    codigo = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único del plan (ej: 3_dias, 5_dias)",
    )

    nombre = models.CharField(max_length=100, help_text="Nombre descriptivo del plan")

    precio = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Precio mensual del plan"
    )

    activo = models.BooleanField(
        default=True, help_text="Si el plan está disponible para nuevos clientes"
    )

    orden = models.PositiveIntegerField(default=0, help_text="Orden de visualización")

    class Meta:
        verbose_name = "Plan"
        verbose_name_plural = "Planes"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"


class Cliente(models.Model):
    """Clientes del gim, tienen turno y plan."""

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

    # Plan contratado
    plan = models.ForeignKey(
        "Plan",
        on_delete=models.PROTECT,
        related_name="clientes",
        help_text="Plan contratado por el cliente",
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.plan.nombre})"
