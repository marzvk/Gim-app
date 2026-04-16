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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # El dueño solo ve profesores, no otros dueños ni superusers
            return qs.filter(is_superuser=False, rol="profesor")
        return qs

    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser:
            if obj is None:  # Creando usuario nuevo
                return (
                    (None, {"fields": ("username", "password1", "password2")}),
                    (
                        "Información personal",
                        {"fields": ("first_name", "last_name", "email")},
                    ),
                    ("Gimnasio", {"fields": ("rol", "turno_asignado")}),
                    ("Estado", {"fields": ("is_active",)}),
                )
            else:  # Editando usuario existente
                return (
                    (None, {"fields": ("username", "password")}),
                    (
                        "Información personal",
                        {"fields": ("first_name", "last_name", "email")},
                    ),
                    ("Gimnasio", {"fields": ("rol", "turno_asignado")}),
                    ("Estado", {"fields": ("is_active",)}),
                )
        return super().get_fieldsets(request, obj)

    #
    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            # El dueño no puede cambiar permisos ni roles de superuser
            return ["is_superuser", "is_staff", "groups", "user_permissions"]
        return super().get_readonly_fields(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            # El dueño solo puede crear/editar profesores
            if "rol" in form.base_fields:
                form.base_fields["rol"].choices = [("profesor", "Profesor")]
        return form


#
@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "hora_inicio", "hora_fin", "activo"]
    list_filter = ["activo"]

    def has_delete_permission(self, request, obj=None):
        # Solo superuser puede borrar turnos
        return request.user.is_superuser

    # def has_add_permission(self, request):
    #     # Solo superuser puede crear turnos
    #     return request.user.is_superuser
