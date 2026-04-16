from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Usuario(AbstractUser):

    ROL_CHOICES = [
        ("profesor", "Profesor"),
        ("dueño", "Dueño"),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROL_CHOICES,
        default="profesor",
    )

    turno_asignado = models.ForeignKey(
        "Turno",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class Turno(models.Model):

    nombre = models.CharField(
        max_length=60,
        unique=True,
        help_text="Nombre del turno (ej: Mañana, Tarde, Noche)",
    )

    hora_inicio = models.TimeField(help_text="Hora de inicio del turno (ej: 09:00)")

    hora_fin = models.TimeField(help_text="Hora de fin del turno (ej: 12:00)")

    activo = models.BooleanField(default=True, help_text="Si el turno está activo o no")

    class Meta:
        verbose_name = "Turno"
        verbose_name_plural = "Turnos"
        ordering = ["hora_inicio"]

    def __str__(self):
        return f"{self.nombre} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"


@receiver(post_save, sender=Usuario)
def asignar_grupo_dueno(sender, instance, **kwargs):
    from django.contrib.auth.models import Group

    if instance.rol == "dueño":
        grupo, _ = Group.objects.get_or_create(name="Dueño")
        instance.groups.add(grupo)
        if not instance.is_staff:
            Usuario.objects.filter(pk=instance.pk).update(is_staff=True)
    else:
        try:
            grupo = Group.objects.get(name="Dueño")
            instance.groups.remove(grupo)
        except Group.DoesNotExist:
            pass
