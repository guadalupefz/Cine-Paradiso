from flask import Blueprint, jsonify

mis_rutas = Blueprint('butacas', __name__)

ESTADOS_BUTACAS = ["libre", "ocupada", "reservada"]

@mis_rutas.route('/funciones/<int:id_funcion>/butacas')
def consultar_butacas(id_funcion):
    if id_funcion <= 0:
        return jsonify({
            "error": "El ID de la funcion debe ser positivo"
        }), 400

    butacas = [
        {
            "id_butaca": 1,
            "numero": "A1",
            "estado": "libre"
        },
        {
            "id_butaca": 2,
            "numero": "A2",
            "estado": "ocupada"
        },
        {
            "id_butaca": 3,
            "numero": "A3",
            "estado": "reservada"
        }
    ]

    for butaca in butacas:
        if butaca["estado"] not in ESTADOS_BUTACAS:
            return jsonify({
                "error": "Estado de butaca invalido"
            }), 500

    return jsonify({
        "id_funcion": id_funcion,
        "butacas": butacas
    }), 200

