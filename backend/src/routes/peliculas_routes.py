from flask import Blueprint, jsonify, request
import mysql.connector
from backend.seguridad import admin_required
from backend.db.db import get_connection
from backend.src.repositories.peliculas_repository import obtener_peliculas
from backend.src.validators.duracion_validator import minutos_de_duracion
from backend.src.services.peliculas_service import (
    listar_peliculas_service,
    crear_pelicula_service,
    editar_pelicula_service,
)
from backend.src.services.omdb_service import (
    buscar_peliculas_omdb_service,
    obtener_detalle_omdb_service,
    importar_pelicula_omdb_service,
)
from backend.src.validators.peliculas_validator import (
    validar_pelicula,
    validar_id_pelicula
)
from backend.src.validators.omdb_validator import (
    validar_busqueda_omdb,
    validar_detalle_omdb,
    validar_importacion_omdb,
)

peliculas_bp = Blueprint("peliculas", __name__)

@peliculas_bp.route("/peliculas", methods=["GET"])
def listar_peliculas():
    resultado = listar_peliculas_service(
        get_connection=get_connection,
        obtener_peliculas=obtener_peliculas,
    )

    return jsonify(resultado["data"]), resultado["status"]

@peliculas_bp.route("/peliculas", methods=["POST"])
@admin_required
def crear_pelicula_manual(id_usuario):
    datos = request.get_json(silent=True)
    datos_validados, error = validar_pelicula(datos)

    if error:
        return jsonify({"error": error}), 400

    resultado = crear_pelicula_service(
        datos_validados,
        get_connection=get_connection,
    )

    return jsonify(resultado["data"]), resultado["status"]
@peliculas_bp.route("/peliculas/<int:id_pelicula>", methods=["PUT"])
@admin_required
def editar_pelicula_manual(id_usuario, id_pelicula):
    datos = request.get_json(silent=True)
    datos_validados, error = validar_pelicula(datos)
    if error:
        return jsonify({"error": error}), 400

    resultado = editar_pelicula_service(
        id_pelicula,
        datos_validados,
        get_connection=get_connection,
    )

    return jsonify(resultado["data"]), resultado["status"]


def escribir_pelicula_manual(id_pelicula=None):
    datos, error = validar_pelicula(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    conexion = None
    try:
        conexion = get_connection()
        with conexion.cursor() as cursor:
            valores = tuple(
                datos[campo]
                for campo in (
                    "titulo",
                    "sinopsis",
                    "poster",
                    "duracion_minutos",
                    "clasificacion",
                    "genero",
                )
            )

            if id_pelicula is None:
                cursor.execute(
                    "SELECT id_pelicula FROM pelicula WHERE titulo = %s",
                    (datos["titulo"],),
                )
                if cursor.fetchone() is not None:
                    return jsonify({
                        "error": "Ya existe una película con ese título"
                    }), 409

                cursor.execute(
                    "INSERT INTO pelicula "
                    "(titulo, sinopsis, poster, duracion_minutos, "
                    "clasificacion, genero) VALUES (%s,%s,%s,%s,%s,%s)",
                    valores,
                )
                id_pelicula = cursor.lastrowid
                estado = 201
            else:
                cursor.execute(
                    "SELECT id_pelicula, duracion_minutos FROM pelicula "
                    "WHERE id_pelicula = %s FOR UPDATE",
                    (id_pelicula,),
                )
                pelicula_actual = cursor.fetchone()
                if pelicula_actual is None:
                    return jsonify({"error": "Película inexistente"}), 404

                try:
                    duracion_actual = minutos_de_duracion(pelicula_actual[1])
                except ValueError:
                    duracion_actual = None

                if duracion_actual != datos["duracion_minutos"]:
                    cursor.execute(
                        "SELECT id_funcion FROM funcion "
                        "WHERE id_pelicula = %s LIMIT 1",
                        (id_pelicula,),
                    )
                    if cursor.fetchone() is not None:
                        return jsonify({
                            "error": "La película tiene funciones programadas. "
                                     "Revisá su programación antes de cambiar la duración."
                        }), 409

                cursor.execute(
                    "UPDATE pelicula SET "
                    "titulo=%s, sinopsis=%s, poster=%s, duracion_minutos=%s, "
                    "clasificacion=%s, genero=%s WHERE id_pelicula=%s",
                    valores + (id_pelicula,),
                )
                estado = 200

        conexion.commit()
        return jsonify({
            "mensaje": "Película guardada",
            "id_pelicula": id_pelicula,
        }), estado
    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
        return jsonify({"error": "No se pudo guardar la película"}), 500
    finally:
        if conexion is not None:
            conexion.close()
    
@peliculas_bp.route("/peliculas/omdb/buscar", methods=["GET"])
@admin_required
def buscar_peliculas_omdb(id_usuario):
    titulo = request.args.get("titulo")
    error = validar_busqueda_omdb(titulo)

    if error:
        return jsonify({"error": error}), 400

    resultado = buscar_peliculas_omdb_service(titulo)
    return jsonify(resultado["data"]), resultado["status"]


@peliculas_bp.route("/peliculas/omdb/detalle", methods=["GET"])
@admin_required
def obtener_detalle_omdb(id_usuario):
    imdb_id = request.args.get("imdb_id")
    error = validar_detalle_omdb(imdb_id)

    if error:
        return jsonify({"error": error}), 400

    resultado = obtener_detalle_omdb_service(imdb_id)
    return jsonify(resultado["data"]), resultado["status"]


@peliculas_bp.route("/peliculas/omdb/importar", methods=["POST"])
@admin_required
def importar_pelicula_omdb(id_usuario):
    datos = request.get_json(silent=True)
    error = validar_importacion_omdb(datos)

    if error:
        return jsonify({"error": error}), 400

    resultado = importar_pelicula_omdb_service(
        datos["imdb_id"],
        id_usuario
    )

    return jsonify(resultado["data"]), resultado["status"]
