
from flask import Flask, Blueprint, request, jsonify
import requests
from dotenv import load_dotenv
import os
app = Flask(__name__)
app.json.sort_keys = False 
from src.services.peliculas import descargar_poster,pelicula_a_guardar, pelicula_hallada
from src.repositories.peliculas import guardar_pelicula, buscar_pelicula
from seguridad import roles_required, crear_limitador, limitar, admin_required

peliculas_bp= Blueprint('peliculas', __name__)

load_dotenv()
OMDB_API_KEY = os.getenv('OMDB_API_KEY')
OMDB_URL= os.getenv('OMDB_URL')

@peliculas_bp.route('/pelicula', methods=['POST'])
@limitar(max_dia=1000, max_hora=6)
#@ admin_required  
def obtener_pelicula():
    titulo = request.args.get('titulo')    
    if not titulo:
        return jsonify({'error': 'El parámetro "titulo" es obligatorio.'}), 400
        
    if buscar_pelicula (titulo):
        return ({' Error': f'la pelicula {titulo} ya se encuentra cargada'}), 200
    
   
    params = {
        'apikey': OMDB_API_KEY,
        't': titulo
    }
    
    try:
        respuesta_omdb = requests.get(OMDB_URL, params=params)
        datos_omdb = respuesta_omdb.json()
        titulo_real = datos_omdb.get('Title')
        url_poster_omdb = datos_omdb.get('Poster')
        
        if datos_omdb.get('Response') == 'False':
            return jsonify({'error': datos_omdb.get('Error', 'Película no encontrada')}), 404
            
        ruta_poster_local = descargar_poster(url_poster_omdb, titulo_real)
        resultado = pelicula_a_guardar (datos_omdb, ruta_poster_local)       
        guardado_exitoso = guardar_pelicula(resultado)
        
        if guardado_exitoso:
            return jsonify( {'mensaje': 'Película y póster guardados localmente con éxito.'}), 200
        else:
            return jsonify({
                'error': 'Error de conexión/inserción en la base de datos.',
                'mensaje': 'Verifica la consola de Python para ver el detalle del error de MySQL.'
            }), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Error de comunicación con OMDb API', 'detalles': str(e)}), 500


@peliculas_bp.route('/pelicula', methods=['GET'])
#@ admin_required 
def buscar_pelicula_omdb():
    titulo = request.args.get('titulo')
    if not titulo:
        return jsonify({'error': 'El parámetro título es obligatorio.'}), 400
         
    params = {
         'apikey': OMDB_API_KEY,
         't': titulo
    }
     
    try:
        respuesta_omdb = requests.get(OMDB_URL, params=params)
        datos_omdb = respuesta_omdb.json()
         
        if datos_omdb.get('Response') == 'False':
            return jsonify({'error': datos_omdb.get('Error', 'Película no encontrada')}), 404
             
        resultado = pelicula_hallada (datos_omdb)               
            
        return jsonify(resultado), 200
                     
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Error de comunicación con OMDb API', 'detalles': str(e)}), 500
 



