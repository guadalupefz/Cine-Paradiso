from decimal import Decimal, InvalidOperation
import mysql.connector
from flask import Blueprint, jsonify, request
from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.repositories.servicios_repository import (
    obtener_servicios, obtener_servicio, crear_servicio, modificar_servicio, eliminar_servicio,
)

servicios_bp = Blueprint("servicios", __name__)

def validar_servicio(datos):
    if not isinstance(datos, dict):
        raise ValueError("Se esperaba un objeto JSON")
    nombre, descripcion, valor = datos.get("nombre"), datos.get("descripcion"), datos.get("precio")
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 100 or not isinstance(valor, str):
        raise ValueError("Nombre o precio inválidos")
    if not isinstance(descripcion, str) or not descripcion.strip() or len(descripcion.strip()) > 250:
        raise ValueError("La descripción es inválida o supera los 250 caracteres")
    try:
        precio = Decimal(valor.strip())
    except InvalidOperation:
        raise ValueError("Precio inválido")
    if not precio.is_finite() or precio <= 0 or precio > Decimal("99999999.99") or precio.as_tuple().exponent < -2:
        raise ValueError("El precio debe ser positivo, tener como máximo dos decimales y no superar 99999999.99")
    return nombre.strip(), precio

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
        nombre, descripcion, precio = validar_servicio(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                if id_servicio is None:
                    id_servicio = crear_servicio(cursor, nombre, descripcion, precio)
                    estado = 201
                else:
                    if obtener_servicio(cursor, id_servicio) is None:
                        return jsonify({"error": "Servicio inexistente"}), 404
                    modificar_servicio(cursor, id_servicio, nombre, descripcion, precio)
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
