from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        "apellido",
        "nombre",
        "plan",
        "turno",
        "activo",
        "estado_consulta",
        "fecha_alta",
    ]

    list_filter = ["activo", "turno", "plan", "estado_consulta"]
