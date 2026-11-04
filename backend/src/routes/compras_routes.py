from flask import Blueprint, request, jsonify
import mysql.connector
from backend.db.db import get_connection
from backend.seguridad import cualquier_logueado, cliente_required
from backend.src.repositories.compra_repository import obtener_compras_por_usuario, obtener_servicios_de_compra, obtener_compra_de_usuario, obtener_entradas_por_compra

from backend.src.validators.compra_validator import validar_datos_compra
from backend.src.services.compra_service import realizar_compra, confirmar_compra

from backend.src.services.comprobante_service import obtener_comprobante

compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras", methods=["POST"])
@cliente_required
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

    except mysql.connector.Error as error:
        if error.errno in (1062, 1205, 1213):
            return jsonify({"error": "CONFLICTO_COMPRA", "mensaje": "La disponibilidad cambió. Volvé a consultar las butacas."}), 409
        return jsonify({"error": "ERROR_BASE_DATOS", "mensaje": "No se pudo procesar la compra."}), 500

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
            "id_butaca": entrada["id_butaca"],
            "fila": entrada["fila"],
            "numero": entrada["numero"]
           }
           for entrada in entradas
        ]), 200

    finally:
        conn.close()

@compras_bp.get("/compras/<int:id_compra>/comprobante")
@cualquier_logueado
def consultar_comprobante(id_usuario, id_compra):

    try:
        comprobante = obtener_comprobante(id_compra, id_usuario)

        if comprobante is None:
            return jsonify({
                "mensaje": "compra no encontrada"
            }), 404

        return jsonify(comprobante), 200

    except mysql.connector.Error:
        return jsonify({
            "mensaje": "no se pudo obtener el comprobante"
        }), 500


@compras_bp.post("/compras/<int:id_compra>/confirmar")
@cliente_required
def confirmar_compra_route(id_usuario, id_compra):
    try:
        resultado = confirmar_compra(id_usuario, id_compra)

        return jsonify({
            "mensaje": "Compra confirmada correctamente.",
            "compra": resultado
        }), 200

    except ValueError as e:
        return jsonify({
            "error": "COMPRA_INVALIDA",
            "mensaje": str(e)
        }), 400

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "No se pudo confirmar la compra."
        }), 500