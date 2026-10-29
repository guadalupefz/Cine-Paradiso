from flask import Blueprint, jsonify

mis_rutas = Blueprint('butacas', __name__)


@mis_rutas.route('/funciones/<int:id_funcion>/butacas', methods=['GET'])
def consultar_butacas(id_funcion):
    if id_funcion <= 0:
        return jsonify({
            "error": "El ID de la funcion debe ser positivo"
        }), 400

    return jsonify({
        "id_funcion": id_funcion,
        "butacas_vendidas": [],
        "mensaje": "Consulta preparada. Falta conectar la base de datos."
    }), 200

