from flask import Blueprint, jsonify


mis_rutas = Blueprint('butacas', __name__)


@mis_rutas.route('/funciones/<int:id_funcion>/butacas')
def consultar_butacas(id_funcion):
    return jsonify({
        "id_funcion": id_funcion,
        "butacas": []
    })
