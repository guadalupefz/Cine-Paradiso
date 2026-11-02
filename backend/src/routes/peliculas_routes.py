import mysql.connector
from flask import Blueprint, jsonify, request
from backend.seguridad import admin_required
from backend.src.validators.duracion_validator import minutos_de_duracion

from backend.db.db import get_connection
from backend.src.repositories.peliculas_repository import obtener_peliculas

peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/peliculas", methods=["GET"])
def listar_peliculas():
    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            peliculas = obtener_peliculas(cursor)

        return jsonify({"peliculas": peliculas}), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las películas."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()


def validar_pelicula(datos):
    if not isinstance(datos, dict):
        raise ValueError("Se esperaba un objeto JSON")
    resultado = {}
    for clave, limite in [("titulo", 150), ("sinopsis", 65000), ("poster", 100), ("clasificacion", 20), ("genero", 50)]:
        valor = datos.get(clave)
        if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
            raise ValueError(f"Revisá el campo {clave}")
        resultado[clave] = valor.strip()
    duracion = datos.get("duracion_minutos")
    if type(duracion) is not int or not 1 <= duracion <= 1440:
        raise ValueError("La duración debe ser un entero entre 1 y 1440 minutos")
    resultado["duracion_minutos"] = str(duracion)
    return resultado

@peliculas_bp.post("/peliculas")
@admin_required
def crear_pelicula_manual(id_usuario):
    return escribir_pelicula_manual()

@peliculas_bp.put("/peliculas/<int:id_pelicula>")
@admin_required
def editar_pelicula_manual(id_usuario, id_pelicula):
    return escribir_pelicula_manual(id_pelicula)

def escribir_pelicula_manual(id_pelicula=None):
    try:
        datos = validar_pelicula(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    conexion = None
    try:
        conexion = get_connection()
        with conexion.cursor() as cursor:
            valores = tuple(datos[k] for k in ("titulo", "sinopsis", "poster", "duracion_minutos", "clasificacion", "genero"))
            if id_pelicula is None:
                cursor.execute("SELECT id_pelicula FROM pelicula WHERE titulo = %s", (datos["titulo"],))
                if cursor.fetchone() is not None:
                    return jsonify({"error": "Ya existe una película con ese título"}), 409
                cursor.execute("INSERT INTO pelicula (titulo, sinopsis, poster, duracion_minutos, clasificacion, genero) VALUES (%s,%s,%s,%s,%s,%s)", valores)
                id_pelicula = cursor.lastrowid
                estado = 201
            else:
                cursor.execute("SELECT id_pelicula, duracion_minutos FROM pelicula WHERE id_pelicula = %s FOR UPDATE", (id_pelicula,))
                pelicula_actual = cursor.fetchone()
                if pelicula_actual is None:
                    return jsonify({"error": "Película inexistente"}), 404
                try:
                    duracion_actual = minutos_de_duracion(pelicula_actual[1])
                except ValueError:
                    duracion_actual = None
                if duracion_actual != int(datos["duracion_minutos"]):
                    cursor.execute("SELECT id_funcion FROM funcion WHERE id_pelicula = %s LIMIT 1 FOR UPDATE", (id_pelicula,))
                    if cursor.fetchone() is not None:
                        return jsonify({"error": "La película tiene funciones programadas. Revisá su programación antes de cambiar la duración."}), 409
                cursor.execute("UPDATE pelicula SET titulo=%s, sinopsis=%s, poster=%s, duracion_minutos=%s, clasificacion=%s, genero=%s WHERE id_pelicula=%s", valores+(id_pelicula,))
                estado = 200
        conexion.commit()
        return jsonify({"mensaje": "Película guardada", "id_pelicula": id_pelicula}), estado
    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
        return jsonify({"error": "No se pudo guardar la película"}), 500
    finally:
        if conexion is not None:
            conexion.close()
