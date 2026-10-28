from flask import Blueprint


mis_rutas = Blueprint('butacas', __name__)


@mis_rutas.route('/funciones/<int:id_funcion>/butacas')
def consultar_butacas(id_funcion):
    return "Consulta de butacas de la funcion"
