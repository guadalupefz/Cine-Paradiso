import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import cliente_required
from backend.src.services import resenas_service
from backend.src.validators.resenas_validator import validar_datos_resena

resenas_bp = Blueprint("resenas", __name__)


@resenas_bp.get("/peliculas/<int:id_pelicula>/resenas")
def listar_resenas(id_pelicula):
    conn = None

    try:
        conn = get_connection()
        with conn.cursor(dictionary=True) as cursor:
            resultado = resenas_service.obtener_resenas_pelicula(
                cursor, id_pelicula
            )

        if resultado is None:
            return jsonify({"error": "No se encontró la película."}), 404

        return jsonify(resultado), 200

    except mysql.connector.Error:
        return jsonify({"error": "No se pudieron consultar las reseñas."}), 500

    finally:
        if conn is not None:
            conn.close()


@resenas_bp.get("/peliculas/<int:id_pelicula>/resenas/propia")
@cliente_required
def consultar_resena_propia(id_usuario, id_pelicula):
    conn = None

    try:
        conn = get_connection()
        with conn.cursor(dictionary=True) as cursor:
            resultado = resenas_service.obtener_resena_propia(
                cursor, id_usuario, id_pelicula
            )

        if resultado is None:
            return jsonify({"error": "No se encontró la película."}), 404

        return jsonify({
            "puede_resenar": bool(resultado["puede_resenar"]),
            "resena": (
                {
                    "puntuacion": resultado["puntuacion"],
                    "comentario": resultado["comentario"],
                    "fecha_actualizacion": resultado["fecha_actualizacion"],
                }
                if resultado["puntuacion"] is not None
                else None
            ),
        }), 200

    except mysql.connector.Error:
        return jsonify({"error": "No se pudo consultar la reseña."}), 500

    finally:
        if conn is not None:
            conn.close()


@resenas_bp.post("/peliculas/<int:id_pelicula>/resenas")
@cliente_required
def guardar_resena(id_usuario, id_pelicula):
    datos = request.get_json(silent=True)
    error = validar_datos_resena(datos)

    if error:
        return jsonify({"error": error}), 400

    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            resultado, error = resenas_service.guardar_resena(
                cursor,
                id_usuario,
                id_pelicula,
                datos["puntuacion"],
                datos.get("comentario", "").strip(),
            )

        if error:
            conn.rollback()

            if error == "PELICULA_NO_ENCONTRADA":
                return jsonify({"error": "No se encontró la película."}), 404

            return jsonify({
                "error": "Solo podés reseñar películas de entradas validadas por QR."
            }), 403

        conn.commit()
        return jsonify(resultado), 200

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()

        return jsonify({"error": "No se pudo guardar la reseña."}), 500

    finally:
        if conn is not None:
            conn.close()
