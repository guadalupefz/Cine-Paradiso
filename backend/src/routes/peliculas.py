from flask import Flask, Blueprint, request, jsonify
import requests
from dotenv import load_dotenv
import os
app = Flask(__name__)
app.json.sort_keys = False
from backend.src.services.peliculas import descargar_poster,pelicula_a_guardar, pelicula_hallada
from backend.src.repositories.peliculas import guardar_pelicula
from backend.seguridad import roles_required, crear_limitador, limitar, admin_required

peliculas_bp= Blueprint('peliculas_externas', __name__)

load_dotenv()
OMDB_API_KEY = os.getenv('OMDB_API_KEY')
OMDB_URL= os.getenv('OMDB_URL')

@peliculas_bp.route('/pelicula', methods=['POST'])
@limitar(max_dia=1000, max_hora=6)
@admin_required
def obtener_pelicula(id_usuario):
    titulo = request.args.get('titulo')
    if not titulo:
        return jsonify({'error': 'El parámetro "titulo" es obligatorio.'}), 400

    if not OMDB_API_KEY or not OMDB_URL:
        return jsonify({"error": "La API externa no está configurada"}), 503

    params = {
        'apikey': OMDB_API_KEY,
        't': titulo
    }

    try:
        respuesta_omdb = requests.get(OMDB_URL, params=params, timeout=10)
        respuesta_omdb.raise_for_status()
        datos_omdb = respuesta_omdb.json()

        if datos_omdb.get('Response') == 'False':
            return jsonify({'error': datos_omdb.get('Error', 'Película no encontrada')}), 404

        imdb_id = datos_omdb.get('imdbID')
        if not isinstance(imdb_id, str) or not imdb_id.strip():
            return jsonify({'error': 'OMDb no devolvió un imdbID válido'}), 502

        titulo_real = datos_omdb.get('Title')
        url_poster_omdb = datos_omdb.get('Poster')
        ruta_poster_local = descargar_poster(url_poster_omdb, titulo_real)
        resultado = pelicula_a_guardar (datos_omdb, ruta_poster_local)
        resultado_guardado = guardar_pelicula(resultado)

        if resultado_guardado["exito"]:
            return jsonify({
                'mensaje': f'Película {resultado_guardado["accion"]} correctamente.',
                'accion': resultado_guardado["accion"],
                'id_pelicula': resultado_guardado["id"]
            }), 200
        else:
            return jsonify({
                'error': 'Error de conexión/inserción en la base de datos.',
                'detalle': resultado_guardado.get("error", "No se pudo guardar en MySQL.")
            }), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Error de comunicación con OMDb API', 'detalles': str(e)}), 500
    except ValueError:
        return jsonify({'error': 'OMDb devolvió una respuesta JSON inválida'}), 502


@peliculas_bp.route('/pelicula', methods=['GET'])
@admin_required
def buscar_pelicula_omdb(id_usuario):
    titulo = request.args.get('titulo')
    if not titulo:
        return jsonify({'error': 'El parámetro título es obligatorio.'}), 400

    if not OMDB_API_KEY or not OMDB_URL:
        return jsonify({"error": "La API externa no está configurada"}), 503

    params = {
         'apikey': OMDB_API_KEY,
         't': titulo
    }

    try:
        respuesta_omdb = requests.get(OMDB_URL, params=params, timeout=10)
        datos_omdb = respuesta_omdb.json()

        if datos_omdb.get('Response') == 'False':
            return jsonify({'error': datos_omdb.get('Error', 'Película no encontrada')}), 404

        resultado = pelicula_hallada (datos_omdb)

        return jsonify(resultado), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Error de comunicación con OMDb API', 'detalles': str(e)}), 500
