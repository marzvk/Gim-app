from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path(
        "cliente/<int:cliente_id>/historial/",
        views.modal_historial_pagos,
        name="modal_historial",
    ),
    path("crear/", views.crear_cliente, name="crear_cliente"),
]
