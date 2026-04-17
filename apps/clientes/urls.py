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
    path(
        "cliente/<int:cliente_id>/editar/", views.editar_cliente, name="editar_cliente"
    ),
    path("reportes/", views.reportes, name="reportes"),
    path("exportar/xml/", views.exportar_xml, name="exportar_xml"),
    path("importar/xml/", views.importar_xml, name="importar_xml"),
    path("exportar/excel/", views.exportar_excel, name="exportar_excel"),
    path("importar/excel/", views.importar_excel, name="importar_excel"),
    path("exportar/csv/", views.exportar_csv, name="exportar_csv"),
    path("importar/csv/", views.importar_csv, name="importar_csv"),
]
