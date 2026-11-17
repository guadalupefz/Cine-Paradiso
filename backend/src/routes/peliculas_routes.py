from flask import Blueprint, jsonify, request
from backend.seguridad import admin_required
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

