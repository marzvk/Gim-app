from .settings import *

# Desactivar axes para tests (evita AxesBackendRequestParameterRequired con client.login())
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]