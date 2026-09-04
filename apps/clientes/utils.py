import os

EXTENSIONES_PERMITIDAS = {
    "xml": {".xml"},
    "excel": {".xlsx", ".xls"},
    "csv": {".csv"},
}
MIME_TYPES_PERMITIDOS = {
    "xml": {"application/xml", "text/xml"},
    "excel": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"},
    "csv": {"text/csv", "application/csv"},
}
MAX_ARCHIVO_BYTES = 2 * 1024 * 1024


def validar_archivo_importacion(archivo, tipo):
    ext = os.path.splitext(archivo.name)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS[tipo]:
        return False, f"Extensión {ext} no permitida para {tipo}."
    content_type = getattr(archivo, "content_type", "") or ""
    if content_type and content_type not in MIME_TYPES_PERMITIDOS[tipo]:
        return False, f"Tipo MIME {content_type} no permitido para {tipo}."
    if archivo.size > MAX_ARCHIVO_BYTES:
        return False, "El archivo supera el tamaño máximo de 2MB."
    return True, ""