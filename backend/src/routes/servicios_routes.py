import os
import uuid

import mysql.connector
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.services import servicios_service
from backend.src.validators.servicios_validator import (
    archivo_permitido,
    validar_servicio,
)

servicios_bp = Blueprint("servicios", __name__)


def validar_y_procesar_servicio():
    datos = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    nombre, descripcion, precio = validar_servicio(datos)

    archivo = request.files.get("imagen")

    if archivo and archivo.filename:
        filename = secure_filename(archivo.filename)

        if not archivo_permitido(filename):
            raise ValueError(
                "Formato de imagen no permitido (solo png, jpg, jpeg, webp)"
            )
    else:
        archivo = None

    return nombre, descripcion, precio, archivo


def guardar_imagen(archivo):
    extension = secure_filename(archivo.filename).rsplit(".", 1)[1].lower()
    nombre = f"{uuid.uuid4().hex}.{extension}"
    carpeta = os.path.join(current_app.static_folder, "img", "servicios")
    os.makedirs(carpeta, exist_ok=True)
    destino = os.path.join(carpeta, nombre)

    try:
        archivo.save(destino)
    except OSError:
        if os.path.exists(destino):
            os.remove(destino)
        raise

    return f"img/servicios/{nombre}"


def descartar_imagen(imagen):
    if imagen:
        ruta = os.path.join(current_app.static_folder, imagen)

        try:
            os.remove(ruta)
        except OSError:
            current_app.logger.warning(
                "No se pudo eliminar la imagen de una operación fallida"
            )


@servicios_bp.get("/servicios")
def listar_servicios():
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            servicios = servicios_service.listar_servicios(cursor)

        return jsonify(servicios), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "No se pudieron consultar los servicios"
        }), 500

    finally:
        if conexion is not None:
            conexion.close()


@servicios_bp.post("/servicios")
@admin_required
def registrar_servicio(id_usuario):
    return escribir_servicio()


@servicios_bp.put("/servicios/<int:id_servicio>")
@admin_required
def actualizar_servicio(id_usuario, id_servicio):
    return escribir_servicio(id_servicio)


def escribir_servicio(id_servicio=None):
    try:
        nombre, descripcion, precio, archivo = validar_y_procesar_servicio()
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    imagen = ""
    conexion = None

    try:
        conexion = get_connection()

        try:
            with conexion.cursor(dictionary=True) as cursor:
                if (
                    id_servicio is not None
                    and servicios_service.obtener_servicio(cursor, id_servicio) is None
                ):
                    return jsonify({"error": "Servicio inexistente"}), 404

                if archivo is not None:
                    imagen = guardar_imagen(archivo)

                if id_servicio is None:
                    id_servicio = servicios_service.crear_servicio(
                        cursor, nombre, descripcion, precio, imagen
                    )
                    estado = 201
                else:
                    servicios_service.modificar_servicio(
                        cursor,
                        id_servicio,
                        nombre,
                        descripcion,
                        precio,
                        imagen,
                    )
                    estado = 200

            conexion.commit()

        except (mysql.connector.Error, OSError):
            conexion.rollback()
            raise

        finally:
            conexion.close()

    except mysql.connector.IntegrityError:
        descartar_imagen(imagen)
        return jsonify({
            "error": "Ya existe un servicio con ese nombre"
        }), 409

    except mysql.connector.Error:
        descartar_imagen(imagen)
        return jsonify({
            "error": "No se pudo guardar el servicio"
        }), 500

    except OSError:
        descartar_imagen(imagen)
        return jsonify({
            "error": "No se pudo guardar la imagen"
        }), 500

    return jsonify({
        "mensaje": "Servicio guardado",
        "id_servicio": id_servicio
    }), estado


@servicios_bp.delete("/servicios/<int:id_servicio>")
@admin_required
def borrar_servicio(id_usuario, id_servicio):
    conexion = None

    try:
        conexion = get_connection()

        try:
            with conexion.cursor() as cursor:
                borradas = servicios_service.eliminar_servicio(
                    cursor, id_servicio
                )

            conexion.commit()

        except mysql.connector.Error:
            conexion.rollback()
            raise

        finally:
            conexion.close()

    except mysql.connector.IntegrityError:
        return jsonify({
            "error": "El servicio tiene compras asociadas y debe conservarse para mantener el historial"
        }), 409

    except mysql.connector.Error:
        return jsonify({
            "error": "No se pudo eliminar el servicio"
        }), 500

    if not borradas:
        return jsonify({"error": "Servicio inexistente"}), 404

    return jsonify({"mensaje": "Servicio eliminado"}), 200
