from flask import Blueprint, jsonify, request

from backend.seguridad import cliente_required
from backend.src.services import resenas_service
from backend.src.validators.resenas_validator import validar_datos_resena

resenas_bp = Blueprint("resenas", __name__)


@resenas_bp.get("/peliculas/<int:id_pelicula>/resenas")
def listar_resenas(id_pelicula):
    resultado = resenas_service.obtener_resenas_pelicula(id_pelicula)
    if resultado is None:
        return jsonify({"error": "No se encontró la película."}), 404
    return jsonify(resultado), 200


@resenas_bp.get("/peliculas/<int:id_pelicula>/resenas/propia")
@cliente_required
def consultar_resena_propia(id_usuario, id_pelicula):
    resultado = resenas_service.obtener_resena_propia(id_usuario, id_pelicula)
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


@resenas_bp.post("/peliculas/<int:id_pelicula>/resenas")
@cliente_required
def guardar_resena(id_usuario, id_pelicula):
    datos = request.get_json(silent=True)
    error = validar_datos_resena(datos)

    if error:
        return jsonify({"error": error}), 400

    resultado, error, estado = resenas_service.guardar_resena(
        id_usuario,
        id_pelicula,
        datos["puntuacion"],
        datos.get("comentario", "").strip(),
    )

    if error:
        return jsonify({"error": error}), estado

    return jsonify(resultado), estado
