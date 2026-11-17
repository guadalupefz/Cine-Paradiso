from flask import Blueprint, jsonify, request

from backend.seguridad import admin_required
from backend.src.services.omdb_service import (
    buscar_pelicula_por_titulo,
    importar_pelicula_por_titulo,
)


peliculas_bp = Blueprint("peliculas_externas", __name__)


@peliculas_bp.route("/pelicula", methods=["GET", "POST"])
@admin_required
def consultar_pelicula(id_usuario):
    titulo = (
        request.args.get("titulo")
        if request.method == "GET"
        else request.args.get("titulo")
    )
    if not titulo or not titulo.strip():
        return jsonify({"error": "El título de búsqueda es obligatorio."}), 400

    if request.method == "GET":
        datos, estado = buscar_pelicula_por_titulo(titulo.strip())
    else:
        datos, estado = importar_pelicula_por_titulo(titulo.strip())
    return jsonify(datos), estado
