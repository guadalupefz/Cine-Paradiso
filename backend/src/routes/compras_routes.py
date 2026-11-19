from flask_jwt_extended import jwt_required
from flask import Blueprint, request, jsonify
import mysql.connector

from backend.db.db import get_connection
from backend.seguridad import verificar_acceso

from backend.src.repositories.compra_repository import (
    obtener_compras_por_usuario,
    obtener_servicios_de_compra,
    obtener_compra_de_usuario,
    obtener_entradas_por_compra
)

from backend.src.validators.compra_validator import validar_datos_compra

from backend.src.services.compra_service import (
    realizar_compra,
    confirmar_compra,
    enviar_comprobante_compra
)

from backend.src.services.comprobante_service import obtener_comprobante
from backend.src.services.cancelacion_service import cancelar_compra


compras_bp = Blueprint("compras", __name__)

@compras_bp.route("/compras", methods=["POST"])
@jwt_required()
def registrar_compra():
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    data = request.get_json(silent=True) or {}

    valido, errores = validar_datos_compra(data)

    if not valido:
        return jsonify(errores), 400

    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            conexion.start_transaction()

            resultado, errores = realizar_compra(
                cursor,
                id_usuario,
                data["id_funcion"],
                data["ids_butacas"]
            )

            if errores:
                conexion.rollback()
                return jsonify(errores), 400

            if resultado is None:
                conexion.rollback()
                return jsonify({
                    "error": "ERROR_COMPRA",
                    "mensaje": "No se pudo procesar la compra."
                }), 500

        conexion.commit()

        with conexion.cursor(dictionary=True) as cursor:
            comprobante = obtener_comprobante(
                cursor, resultado["id_compra"], id_usuario
            )

        informacion_correo = enviar_comprobante_compra(
            comprobante, resultado["entradas"]
        )

        resultado.update(informacion_correo)

        return jsonify(resultado), 201

    except mysql.connector.Error as error:
        if conexion:
            conexion.rollback()

        if error.errno in (1062, 1205, 1213):
            return jsonify({
                "error": "CONFLICTO_COMPRA",
                "mensaje": "La disponibilidad cambió. Volvé a consultar las butacas."
            }), 409

        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo procesar la compra."
        }), 500

    except Exception:
        if conexion:
            conexion.rollback()

        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "No se pudo procesar la compra."
        }), 500

    finally:
        if conexion:
            conexion.close()


@compras_bp.get("/compras")
@jwt_required()
def listar_compras_por_usuario():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador', 'cliente'))
    if respuesta_acceso is not None:
        return respuesta_acceso

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
        return jsonify({
            "error": "No se pudieron consultar las compras"
        }), 500

    return jsonify(compras), 200


@compras_bp.get("/compras/<int:id_compra>/servicios")
@jwt_required()
def listar_servicios_de_compra(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('administrador', 'cliente'))
    if respuesta_acceso is not None:
        return respuesta_acceso

    try:
        conexion = get_connection()

        try:
            cursor = conexion.cursor(dictionary=True)

            try:
                compra = obtener_compra_de_usuario(
                    cursor,
                    id_compra,
                    id_usuario
                )

                if compra is None:
                    return jsonify({
                        "error": "Compra inexistente"
                    }), 404

                servicios = obtener_servicios_de_compra(cursor, id_compra)

            finally:
                cursor.close()

        finally:
            conexion.close()

    except mysql.connector.Error:
        return jsonify({
            "error": "No se pudieron consultar los servicios"
        }), 500

    return jsonify(servicios), 200


@compras_bp.get("/compras/<int:id_compra>/entradas")
@jwt_required()
def listar_entradas(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('administrador', 'cliente'))
    if respuesta_acceso is not None:
        return respuesta_acceso

    conn = get_connection()

    try:
        with conn.cursor(dictionary=True) as cursor:
            compra = obtener_compra_de_usuario(
                cursor,
                id_compra,
                id_usuario
            )

            if compra is None:
                return jsonify({
                    "mensaje": "compra no encontrada"
                }), 404

            entradas = obtener_entradas_por_compra(cursor, id_compra)

        return jsonify([
            {
                "id_entrada": entrada["id_entrada"],
                "id_funcion": entrada["id_funcion"],
                "id_butaca": entrada["id_butaca"],
                "fila": entrada["fila"],
                "numero": entrada["numero"],
                "qr_token": entrada["qr_token"]
            }
            for entrada in entradas
        ]), 200

    finally:
        conn.close()


@compras_bp.get("/compras/<int:id_compra>/comprobante")
@jwt_required()
def consultar_comprobante(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('administrador', 'cliente'))
    if respuesta_acceso is not None:
        return respuesta_acceso

    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            comprobante = obtener_comprobante(
                cursor, id_compra, id_usuario
            )

        if comprobante is None:
            return jsonify({
                "mensaje": "compra no encontrada"
            }), 404

        return jsonify(comprobante), 200

    except mysql.connector.Error:
        return jsonify({
            "mensaje": "no se pudo obtener el comprobante"
        }), 500

    finally:
        if conexion is not None:
            conexion.close()


@compras_bp.post("/compras/<int:id_compra>/confirmar")
@jwt_required()
def confirmar_compra_route(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            conexion.start_transaction()

            resultado, errores = confirmar_compra(
                cursor,
                id_usuario,
                id_compra
            )

            if errores:
                conexion.rollback()

                codigo = errores[0]["code"]

                if codigo == "COMPRA_NO_EXISTE":
                    estado_http = 404
                elif codigo == "COMPRA_NO_AUTORIZADA":
                    estado_http = 403
                elif codigo == "COMPRA_NO_PENDIENTE":
                    estado_http = 409
                else:
                    estado_http = 400

                return jsonify(errores), estado_http

            if resultado is None:
                conexion.rollback()
                return jsonify({
                    "error": "ERROR_CONFIRMAR_COMPRA",
                    "mensaje": "No se pudo confirmar la compra."
                }), 500

            if resultado.get("reserva_vencida"):
                conexion.commit()

                return jsonify({
                    "error": "RESERVA_VENCIDA",
                    "mensaje": "La reserva venció y las butacas fueron liberadas."
                }), 400

        conexion.commit()

        with conexion.cursor(dictionary=True) as cursor:
            comprobante = obtener_comprobante(
                cursor, resultado["id_compra"], id_usuario
            )

        informacion_correo = enviar_comprobante_compra(
            comprobante, resultado["entradas"]
        )

        resultado.update(informacion_correo)

        return jsonify({
            "mensaje": "Compra confirmada correctamente.",
            "compra": resultado
        }), 200

    except mysql.connector.Error:
        if conexion:
            conexion.rollback()

        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo confirmar la compra."
        }), 500

    except Exception:
        if conexion:
            conexion.rollback()

        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "No se pudo confirmar la compra."
        }), 500

    finally:
        if conexion:
            conexion.close()


@compras_bp.post("/compras/<int:id_compra>/cancelar")
@jwt_required()
def cancelar_compra_route(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    conexion = None

    mensajes_error = {
        "COMPRA_NO_ENCONTRADA": ("Compra no encontrada", 404),
        "ESTADO_NO_CANCELABLE": (
            "La compra no se puede cancelar en su estado actual", 409
        ),
        "COMPRA_SIN_ENTRADAS": ("La compra no tiene entradas", 409),
        "ENTRADAS_UTILIZADAS": (
            "La compra tiene entradas utilizadas", 409
        ),
        "FUERA_DE_PLAZO": (
            "No se puede cancelar dentro de las dos horas previas a la función",
            409
        )
    }

    try:
        conexion = get_connection()
        conexion.start_transaction()

        with conexion.cursor(dictionary=True) as cursor:
            resultado, error = cancelar_compra(
                cursor, id_usuario, id_compra
            )

        if error is not None:
            conexion.rollback()
            mensaje, codigo = mensajes_error[error]
            return jsonify({"error": mensaje}), codigo

        conexion.commit()
        return jsonify(resultado), 200

    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()

        return jsonify({
            "error": "No se pudo cancelar la compra"
        }), 500

    except Exception:
        if conexion is not None:
            conexion.rollback()

        return jsonify({
            "error": "No se pudo cancelar la compra"
        }), 500

    finally:
        if conexion is not None:
            conexion.close()
