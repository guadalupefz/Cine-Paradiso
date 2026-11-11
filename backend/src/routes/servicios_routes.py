import os
import uuid
from decimal import Decimal, InvalidOperation
import mysql.connector
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.repositories.servicios_repository import (
    obtener_servicios, obtener_servicio, crear_servicio, modificar_servicio, eliminar_servicio,
)

servicios_bp = Blueprint("servicios", __name__)

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}

def archivo_permitido(nombre_archivo):
    return "." in nombre_archivo and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS

def validar_servicio(datos):
    if not isinstance(datos, dict):
        raise ValueError("Se esperaba un objeto JSON")
    nombre = datos.get("nombre")
    descripcion = datos.get("descripcion")
    valor = datos.get("precio")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 100:
        raise ValueError("Nombre inválido")
    if not isinstance(descripcion, str) or not descripcion.strip() or len(descripcion.strip()) > 250:
        raise ValueError("La descripción es inválida o supera los 250 caracteres")
    if not isinstance(valor, str):
        raise ValueError("Precio inválido")
    try:
        precio = Decimal(valor.strip())
    except (InvalidOperation, TypeError):
        raise ValueError("Precio inválido")
    if not precio.is_finite() or precio <= 0 or precio > Decimal("99999999.99") or precio.as_tuple().exponent < -2:
        raise ValueError("El precio debe ser positivo, tener como máximo dos decimales y no superar 99999999.99")

    return nombre.strip(), descripcion.strip(), precio


def validar_y_procesar_servicio():
    datos = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    nombre, descripcion, precio = validar_servicio(datos)
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        filename = secure_filename(archivo.filename)
        if not archivo_permitido(filename):
            raise ValueError("Formato de imagen no permitido (solo png, jpg, jpeg, webp)")
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
            current_app.logger.warning("No se pudo eliminar la imagen de una operación fallida")

@servicios_bp.get("/servicios")
def listar_servicios():
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                servicios = obtener_servicios(cursor)
        finally:
            conexion.close()
    except mysql.connector.Error:
        return jsonify({"error": "No se pudieron consultar los servicios"}), 500
    return jsonify(servicios), 200

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
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                if id_servicio is not None and obtener_servicio(cursor, id_servicio) is None:
                    return jsonify({"error": "Servicio inexistente"}), 404
                if archivo is not None:
                    imagen = guardar_imagen(archivo)
                if id_servicio is None:
                    id_servicio = crear_servicio(cursor, nombre, descripcion, precio, imagen)
                    estado = 201
                else:
                    modificar_servicio(cursor, id_servicio, nombre, descripcion, precio, imagen)
                    estado = 200
            conexion.commit()
        except (mysql.connector.Error, OSError):
            conexion.rollback()
            raise
        finally:
            conexion.close()
    except mysql.connector.IntegrityError:
        descartar_imagen(imagen)
        return jsonify({"error": "Ya existe un servicio con ese nombre"}), 409
    except mysql.connector.Error:
        descartar_imagen(imagen)
        return jsonify({"error": "No se pudo guardar el servicio"}), 500
    except OSError:
        descartar_imagen(imagen)
        return jsonify({"error": "No se pudo guardar la imagen"}), 500
    return jsonify({"mensaje": "Servicio guardado", "id_servicio": id_servicio}), estado

@servicios_bp.delete("/servicios/<int:id_servicio>")
@admin_required
def borrar_servicio(id_usuario, id_servicio):
    try:
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                borradas = eliminar_servicio(cursor, id_servicio)
            conexion.commit()
        except mysql.connector.Error:
            conexion.rollback()
            raise
        finally:
            conexion.close()
    except mysql.connector.IntegrityError:
        return jsonify({"error": "El servicio tiene compras asociadas y debe conservarse para mantener el historial"}), 409
    except mysql.connector.Error:
        return jsonify({"error": "No se pudo eliminar el servicio"}), 500
    if not borradas:
        return jsonify({"error": "Servicio inexistente"}), 404
    return jsonify({"mensaje": "Servicio eliminado"}), 200
