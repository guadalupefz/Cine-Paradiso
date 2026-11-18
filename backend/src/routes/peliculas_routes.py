
from flask import Blueprint, jsonify, request

from backend.seguridad import admin_required

from backend.src.services.peliculas_service import (
    listar_peliculas_service,
    crear_pelicula_service,
    editar_pelicula_service,
)

from backend.src.services.omdb_service import (
    buscar_peliculas,
    obtener_pelicula_por_id,
    preparar_pelicula_para_guardar,
)

from backend.src.validators.peliculas_validators import (
    validar_pelicula,
)

from backend.src.validators.omdb_validator import (
    validar_busqueda_omdb,
    validar_detalle_omdb,
    validar_importacion_omdb,
)

peliculas_bp = Blueprint("peliculas", __name__)

@peliculas_bp.route("/peliculas", methods=["GET"])
def listar_peliculas():
    resultado = listar_peliculas_service()
    return jsonify(resultado["data"]), resultado["status"]

@peliculas_bp.route("/peliculas", methods=["POST"])
@admin_required
def crear_pelicula_manual(id_usuario):
    datos = request.get_json(silent=True)
    datos_validados, error = validar_pelicula(datos)

    if error:
        return jsonify({"error": error}), 400

    resultado = crear_pelicula_service(datos_validados)
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
        datos_validados
    )
    return jsonify(resultado["data"]), resultado["status"]

@peliculas_bp.route("/peliculas/omdb/buscar", methods=["GET"])
@admin_required
def buscar_peliculas_omdb(id_usuario):
    titulo = request.args.get("titulo")
    error = validar_busqueda_omdb(titulo)

    if error:
        return jsonify({"error": error}), 400

    resultado = buscar_peliculas(titulo.strip())
    return jsonify(resultado["data"]), resultado["status"]


@peliculas_bp.route("/peliculas/omdb/detalle", methods=["GET"])
@admin_required
def obtener_detalle_omdb(id_usuario):
    imdb_id = request.args.get("imdb_id")
    error = validar_detalle_omdb(imdb_id)

    if error:
        return jsonify({"error": error}), 400

    resultado = obtener_pelicula_por_id(imdb_id.strip())
    return jsonify(resultado["data"]), resultado["status"]


@peliculas_bp.route("/peliculas/omdb/importar", methods=["POST"])
@admin_required
def importar_pelicula_omdb(id_usuario):
    datos = request.get_json(silent=True)
    error = validar_importacion_omdb(datos)

    if error:
        return jsonify({"error": error}), 400

    resultado = preparar_pelicula_para_guardar(
        datos["imdb_id"]
    )

    return jsonify(resultado["data"]), resultado["status"]
