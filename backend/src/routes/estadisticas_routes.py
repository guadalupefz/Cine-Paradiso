from datetime import datetime

import mysql.connector
from flask import Blueprint, jsonify, request

from db.db import get_connection
from seguridad import admin_required
from src.repositories.estadisticas_repository import (
    obtener_ventas_por_genero,
    obtener_ventas_por_franja,
    obtener_ocupacion_por_funcion,
    obtener_ocupacion_por_pelicula,
    obtener_cantidad_cancelaciones,
)

estadisticas_bp = Blueprint("estadisticas", __name__)


def obtener_filtros_fecha():
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    try:
        if desde:
            datetime.strptime(desde, "%Y-%m-%d")

        if hasta:
            datetime.strptime(hasta, "%Y-%m-%d")

    except ValueError:
        return None, None, "Las fechas deben tener formato AAAA-MM-DD."

    if desde and hasta and desde > hasta:
        return None, None, "La fecha desde no puede ser posterior a hasta."

    return desde, hasta, None


@estadisticas_bp.route("/estadisticas/ventas", methods=["GET"])
@admin_required
def consultar_estadisticas_ventas(id_usuario):
    desde, hasta, error = obtener_filtros_fecha()

    if error:
        return jsonify({
            "error": "FILTRO_INVALIDO",
            "mensaje": error
        }), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            por_genero = obtener_ventas_por_genero(cursor, desde, hasta)
            por_franja = obtener_ventas_por_franja(cursor, desde, hasta)
            cancelaciones = obtener_cantidad_cancelaciones(cursor)

        return jsonify({
            "ventas_por_genero": por_genero,
            "ventas_por_franja_horaria": por_franja,
            "cantidad_cancelaciones": cancelaciones["cantidad_cancelaciones"],
            "filtros": {
                "desde": desde,
                "hasta": hasta
            }
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las estadísticas de ventas."
        }), 500

    finally:
        if conn is not None and conn.is_connected():
            conn.close()


@estadisticas_bp.route("/estadisticas/ocupacion", methods=["GET"])
@admin_required
def consultar_estadisticas_ocupacion(id_usuario):
    desde, hasta, error = obtener_filtros_fecha()

    if error:
        return jsonify({
            "error": "FILTRO_INVALIDO",
            "mensaje": error
        }), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            por_funcion = obtener_ocupacion_por_funcion(cursor, desde, hasta)
            por_pelicula = obtener_ocupacion_por_pelicula(cursor, desde, hasta)

        return jsonify({
            "ocupacion_por_funcion": por_funcion,
            "ocupacion_por_pelicula": por_pelicula,
            "filtros": {
                "desde": desde,
                "hasta": hasta
            }
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las estadísticas de ocupación."
        }), 500

    finally:
        if conn is not None and conn.is_connected():
            conn.close()
