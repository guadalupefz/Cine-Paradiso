
from flask import Blueprint, request, jsonify

from backend.src.validators.compra_validator import validar_datos_compra
from backend.src.services.compra_service import realizar_compra

compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras", methods=["POST"])
def registrar_compra():
    data = request.get_json(silent=True)

    valido, mensaje = validar_datos_compra(data)

    if not valido:
        return jsonify({
            "error": "DATOS_INVALIDOS",
            "mensaje": mensaje
        }), 400

    # Temporalmente recibimos el ID del usuario.
    # Al integrar el login, deberá obtenerse de la sesión.
    id_usuario = data.get("id_usuario")

    if not isinstance(id_usuario, int) or isinstance(id_usuario, bool) or id_usuario <= 0:
        return jsonify({
            "error": "USUARIO_INVALIDO",
            "mensaje": "El ID del usuario debe ser un número positivo."
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
