import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.services import servicios_service

servicios_bp = Blueprint("servicios", __name__)


@servicios_bp.get("/servicios")
def listar_servicios():
    conexion = get_connection()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            servicios = servicios_service.listar_servicios(cursor)
        return jsonify(servicios), 200
    except mysql.connector.Error:
        return jsonify({"error": "No se pudieron consultar los servicios"}), 500
    finally:
        conexion.close()


@servicios_bp.post("/servicios")
@admin_required
def registrar_servicio(id_usuario):
    conexion = get_connection()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            id_servicio = servicios_service.guardar_servicio(cursor, request)
        conexion.commit()
        return jsonify({"mensaje": "Servicio guardado", "id_servicio": id_servicio}), 201
    except ValueError as error:
        conexion.rollback()
        return jsonify({"error": str(error)}), 400
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return jsonify({"error": "Ya existe un servicio con ese nombre"}), 409
    except (mysql.connector.Error, OSError):
        conexion.rollback()
        return jsonify({"error": "No se pudo guardar el servicio"}), 500
    finally:
        conexion.close()


@servicios_bp.put("/servicios/<int:id_servicio>")
@admin_required
def actualizar_servicio(id_usuario, id_servicio):
    conexion = get_connection()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            servicios_service.guardar_servicio(cursor, request, id_servicio)
        conexion.commit()
        return jsonify({"mensaje": "Servicio guardado", "id_servicio": id_servicio}), 200
    except ValueError as error:
        conexion.rollback()
        return jsonify({"error": str(error)}), 400
    except LookupError:
        conexion.rollback()
        return jsonify({"error": "Servicio inexistente"}), 404
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return jsonify({"error": "Ya existe un servicio con ese nombre"}), 409
    except (mysql.connector.Error, OSError):
        conexion.rollback()
        return jsonify({"error": "No se pudo guardar el servicio"}), 500
    finally:
        conexion.close()


@servicios_bp.delete("/servicios/<int:id_servicio>")
@admin_required
def borrar_servicio(id_usuario, id_servicio):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            servicios_service.eliminar_servicio(cursor, id_servicio)
        conexion.commit()
        return jsonify({"mensaje": "Servicio eliminado"}), 200
    except LookupError:
        conexion.rollback()
        return jsonify({"error": "Servicio inexistente"}), 404
    except mysql.connector.IntegrityError:
        conexion.rollback()
        return jsonify({
            "error": "El servicio tiene compras asociadas y debe conservarse para mantener el historial"
        }), 409
    except mysql.connector.Error:
        conexion.rollback()
        return jsonify({"error": "No se pudo eliminar el servicio"}), 500
    finally:
        conexion.close()