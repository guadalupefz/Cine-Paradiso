import os
import uuid
from flask import current_app, url_for
from werkzeug.utils import secure_filename
from backend.src.repositories import servicios_repository as repo
from backend.src.validators.servicios_validator import archivo_permitido, validar_servicio


def _guardar_imagen(archivo):
    nombre_seguro = secure_filename(archivo.filename or "")
    extension = nombre_seguro.rsplit(".", 1)[1].lower()
    nombre = f"{uuid.uuid4().hex}.{extension}"
    carpeta = os.path.join(current_app.static_folder, "img", "servicios")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, nombre)

    archivo.save(destino)
    return url_for("static", filename=f"img/servicios/{nombre}")


def descartar_imagen(imagen):
    if imagen:
        ruta_relativa = imagen.removeprefix("/static/").lstrip("/")
        ruta = os.path.join(current_app.static_folder, ruta_relativa)
        try:
            os.remove(ruta)
        except OSError:
            current_app.logger.warning(
                "No se pudo eliminar la imagen de una operación fallida"
            )


def procesar_datos_y_archivo(request):
    datos = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    nombre, descripcion, precio = validar_servicio(datos)

    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        filename = secure_filename(archivo.filename)
        if not archivo_permitido(filename):
            raise ValueError("Formato de imagen no permitido (solo png, jpg, jpeg, webp)")
    else:
        archivo = None

    imagen = _guardar_imagen(archivo) if archivo else ""
    return nombre, descripcion, precio, imagen


def listar_servicios(cursor):
    return repo.obtener_servicios(cursor)


def guardar_servicio(cursor, request, id_servicio=None):
    imagen_antigua = None

    if id_servicio is not None:
        servicio_actual = repo.obtener_servicio(cursor, id_servicio)
        if servicio_actual is None:
            raise LookupError("Servicio inexistente")
            
        imagen_antigua = servicio_actual.get("imagen")

    nombre, descripcion, precio, imagen = procesar_datos_y_archivo(request)

    if not imagen and id_servicio is not None:
        imagen = imagen_antigua

    try:
        if id_servicio is None:
            id_servicio = repo.crear_servicio(cursor, nombre, descripcion, precio, imagen)
        else:
            repo.modificar_servicio(cursor, id_servicio, nombre, descripcion, precio, imagen)
            
        if imagen and imagen_antigua and imagen != imagen_antigua:
            descartar_imagen(imagen_antigua)

    except Exception:
        if imagen and imagen != imagen_antigua:
            descartar_imagen(imagen)
        raise

    return id_servicio


def eliminar_servicio(cursor, id_servicio):
    servicio = repo.obtener_servicio(cursor, id_servicio)
    if not servicio:
        raise LookupError("Servicio inexistente")

    imagen = servicio.get("imagen") or ""
    borradas = repo.eliminar_servicio(cursor, id_servicio)
    if not borradas:
        raise LookupError("Servicio inexistente")

    return imagen