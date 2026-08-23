from functools import wraps
from django.http import HttpResponseForbidden


def rol_requerido(rol_permitido):
    """Decorator que verifica que el usuario tenga el rol indicado."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if request.user.rol != rol_permitido:
                return HttpResponseForbidden("No tenés permiso para acceder a esta página.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
