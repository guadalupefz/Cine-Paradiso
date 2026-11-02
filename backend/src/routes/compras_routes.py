from flask import Blueprint, request, jsonify
import mysql.connector
from backend.db.db import get_connection
from backend.seguridad import cualquier_logueado
from backend.src.repositories.compra_repository import obtener_compras_por_usuario, obtener_servicios_de_compra, obtener_compra_de_usuario, obtener_entradas_por_compra

from backend.src.validators.compra_validator import validar_datos_compra
from backend.src.services.compra_service import realizar_compra

compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras", methods=["POST"])
@cualquier_logueado
def registrar_compra(id_usuario):
    data = request.get_json(silent=True)

    valido, mensaje = validar_datos_compra(data)

    if not valido:
        return jsonify({
            "error": "DATOS_INVALIDOS",
            "mensaje": mensaje
        }), 400

    try:
        resultado = realizar_compra(
            id_usuario,
            data["id_funcion"],
            data["ids_butacas"]
        )

        return jsonify(resultado), 201

    except ValueError as e:
        return jsonify({
            "error": "COMPRA_INVALIDA",
            "mensaje": str(e)
        }), 400

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "No se pudo procesar la compra."
        }), 500


@compras_bp.get("/compras")
@cualquier_logueado
def listar_compras_por_usuario(id_usuario):
    try:
        conexion = get_connection()
        try:
            cursor = conexion.cursor(dictionary=True)
            try:
                compras = obtener_compras_por_usuario(cursor, id_usuario)
            finally:
                cursor.close()
        finally:
            conexion.close()
    except mysql.connector.Error:
        return jsonify({"error": "No se pudieron consultar las compras"}), 500

    return jsonify(compras), 200

@compras_bp.get("/compras/<int:id_compra>/servicios")
@cualquier_logueado
def listar_servicios_de_compra(id_usuario, id_compra):
    try:
        conexion = get_connection()
        try:
            cursor = conexion.cursor(dictionary=True)

            try:
                compra = obtener_compra_de_usuario(cursor, id_compra, id_usuario)

                if compra is None:
                    return jsonify({"error": "Compra inexistente"}), 404

                servicios = obtener_servicios_de_compra(cursor, id_compra)
            finally:
                cursor.close()
        finally:
            conexion.close()
    except mysql.connector.Error:
        return jsonify({"error": "No se pudieron consultar los servicios"}), 500

    return jsonify(servicios), 200


@compras_bp.get("/compras/<int:id_compra>/entradas")
@cualquier_logueado
def listar_entradas(id_usuario, id_compra):
    conn = get_connection()

    try:
        with conn.cursor(dictionary=True) as cursor:
            compra = obtener_compra_de_usuario(cursor, id_compra, id_usuario)

            if compra is None:
                return jsonify({"mensaje": "compra no encontrada"}), 404

            entradas = obtener_entradas_por_compra(cursor, id_compra)

        return jsonify([
            {
                "id_entrada": entrada["id_entrada"],
                "id_funcion": entrada["id_funcion"],
                "id_butaca": entrada["id_butaca"]
            }
            for entrada in entradas
        ]), 200

    finally:
        conn.close()