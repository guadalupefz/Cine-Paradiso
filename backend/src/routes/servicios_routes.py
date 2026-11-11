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

def validar_y_procesar_servicio():
    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    valor = request.form.get("precio")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 100:
        raise ValueError("Nombre inválido")
    if not isinstance(descripcion, str) or not descripcion.strip() or len(descripcion.strip()) > 250:
        raise ValueError("La descripción es inválida o supera los 250 caracteres")
    try:
        precio = Decimal(str(valor).strip())
    except (InvalidOperation, TypeError):
        raise ValueError("Precio inválido")
    if not precio.is_finite() or precio <= 0 or precio > Decimal("99999999.99") or precio.as_tuple().exponent < -2:
        raise ValueError("El precio debe ser positivo, tener como máximo dos decimales y no superar 99999999.99")

    nombre_imagen = None
    if "imagen" in request.files:
        archivo = request.files["imagen"]
        if archivo and archivo.filename != "":
            if not archivo_permitido(archivo.filename):
                raise ValueError("Formato de imagen no permitido (solo png, jpg, jpeg, webp)")
            
            filename = secure_filename(archivo.filename)
            extension = filename.rsplit(".", 1)[1].lower()
            nombre_unico = f"{uuid.uuid4().hex}.{extension}"
            
            carpeta_upload = os.path.join(current_app.root_path, "static", "img", "servicios")
            os.makedirs(carpeta_upload, exist_ok=True)
            
            archivo.save(os.path.join(carpeta_upload, nombre_unico))
            nombre_imagen = f"img/servicios/{nombre_unico}"

    return nombre.strip(), descripcion.strip(), precio, nombre_imagen

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
        nombre, descripcion, precio, imagen = validar_y_procesar_servicio()
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                if id_servicio is None:
                    id_servicio = crear_servicio(cursor, nombre, descripcion, precio, imagen)
                    estado = 201
                else:
                    if obtener_servicio(cursor, id_servicio) is None:
                        return jsonify({"error": "Servicio inexistente"}), 404
                    modificar_servicio(cursor, id_servicio, nombre, descripcion, precio, imagen)
                    estado = 200
            conexion.commit()
        except mysql.connector.Error:
            conexion.rollback()
            raise
        finally:
            conexion.close()
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Ya existe un servicio con ese nombre"}), 409
    except mysql.connector.Error:
        return jsonify({"error": "No se pudo guardar el servicio"}), 500
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