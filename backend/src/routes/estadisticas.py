from flask import Blueprint, jsonify

rutas_estadisticas = Blueprint('estadisticas', __name__)


@rutas_estadisticas.route('/estadisticas/ventas', methods=['GET'])
def consultar_ventas():
    return jsonify({
        "mensaje": "Estadisticas de ventas",
        "estado": "pendiente",
        "datos": None
    }), 200


@rutas_estadisticas.route('/estadisticas/ocupacion', methods=['GET'])
def consultar_ocupacion():
    return jsonify({
        "mensaje": "Estadisticas de ocupacion",
        "estado": "pendiente",
        "datos": None
    }), 200
