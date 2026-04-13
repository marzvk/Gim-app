from django.urls import path
from . import views

urlpatterns = [
    path("pago/<int:cliente_id>/", views.modal_registrar_pago, name="modal_pago")
]
