from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Turno, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["username", "email", "rol", "turno_asignado", "is_active"]
    list_filter = ["rol", "turno_asignado", "is_active"]

    fieldsets = UserAdmin.fieldsets + (
        ("Información del Gimnasio", {"fields": ("rol", "turno_asignado")}),
    )


@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "hora_inicio", "hora_fin", "activo"]
    list_filter = ["activo"]
