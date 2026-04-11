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

    search_fields = ["nombre", "apellido", "telefono", "email"]

    readonly_fields = ["fecha_alta", "usuario_creador"]

    #
    def save_model(self, request, obj, form, change):
        if not change:  # Solo cuando se crea (no cuando se edita)
            obj.usuario_creador = request.user
        super().save_model(request, obj, form, change)
