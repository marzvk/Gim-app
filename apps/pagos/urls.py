from django.urls import path
from . import views

urlpatterns = [
    path("pago/<int:cliente_id>/", views.modal_registrar_pago, name="modal_pago"),
    path("editar/<int:pago_id>/", views.editar_pago, name="editar_pago"),
    path("borrar/<int:pago_id>/", views.borrar_pago, name="borrar_pago"),
]
