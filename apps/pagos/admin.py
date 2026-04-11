from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = [
        "cliente",
        "mes_cubierto_formatted",
        "fecha_pago",
        "monto",
        "usuario_registrador",
    ]

    list_filter = ["fecha_pago", "mes_cubierto"]

    search_fields = ["cliente__nombre", "cliente__apellido"]

    readonly_fields = ["created_at", "usuario_registrador"]

    #
    def mes_cubierto_formatted(self, obj):
        """
        Muestra el mes en formato legible: 'Abril 2026'
        """
        meses = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        return f"{meses[obj.mes_cubierto.month - 1]} - {obj.mes_cubierto.year}"

    mes_cubierto_formatted.short_description = "Mes Cubierto"

    def save_model(self, request, obj, form, change):
        """
        Guarda automáticamente quién registró el pago
        """
        if not change:
            obj.usuario_registrador = request.user
        super().save_model(request, obj, form, change)
