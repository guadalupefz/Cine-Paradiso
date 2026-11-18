import os
import unittest
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token
from backend.app import app
from backend import seguridad
from backend.autenticacion import jwt
from backend.src.routes import peliculas_routes
from backend.src.services import omdb_service


class RutasOMDb(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        self.ficha = {
            'Response': 'True', 'imdbID': 'tt0133093', 'Title': 'The Matrix',
            'Year': '1999', 'Genre': 'Action, Sci-Fi', 'Plot': 'Una historia.',
            'Runtime': '136 min', 'Rated': 'R', 'Poster': 'N/A',
        }
        self.identidad = MagicMock()
        self.identidad.cursor.return_value.__enter__.return_value.fetchone.return_value = {
            'id_usuario': 8, 'rol': 'administrador',
        }
        self.conexion = MagicMock()
        self.cursor = self.conexion.cursor.return_value
        self.cursor.fetchone.return_value = None
        self.cursor.lastrowid = 37
        for parche in (
            patch.dict(os.environ, {'OMDB_API_KEY': 'clave-ficticia'}),
            patch.object(seguridad, 'get_connection', return_value=self.identidad),
            patch.object(jwt, '_token_in_blocklist_callback', return_value=False),
            patch.object(peliculas_routes, 'get_connection', return_value=self.conexion),
        ):
            parche.start()
            self.addCleanup(parche.stop)
        self.proveedor = patch.object(omdb_service.requests, 'get')
        self.consultar = self.proveedor.start()
        self.addCleanup(self.proveedor.stop)
        self.respuesta = self.consultar.return_value
        self.respuesta.json.return_value = self.ficha
        with app.app_context():
            token = create_access_token(identity='8')
        self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + token

    def importar(self):
        return self.client.post('/api/peliculas/omdb/importar', json={'imdb_id': 'tt0133093'})

    def test_busqueda_devuelve_el_formato_del_servicio(self):
        self.respuesta.json.return_value = {
            'Response': 'True', 'totalResults': '1', 'Search': [self.ficha],
        }
        respuesta = self.client.get('/api/peliculas/omdb/buscar?titulo=Matrix')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json['peliculas'][0]['id_imdb'], 'tt0133093')
        self.conexion.commit.assert_not_called()

    def test_detalle_devuelve_la_ficha(self):
        respuesta = self.client.get('/api/peliculas/omdb/detalle?imdb_id=tt0133093')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json['titulo'], 'The Matrix')

    def test_pantalla_puede_consultar_por_titulo_sin_guardar(self):
        respuesta = self.client.get('/api/pelicula?titulo=Matrix')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json['titulo'], 'The Matrix')
        self.cursor.execute.assert_not_called()

    def test_pantalla_puede_importar_por_titulo(self):
        respuesta = self.client.post('/api/pelicula?titulo=Matrix')
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json['id_externo_api'], 'tt0133093')
        self.conexion.commit.assert_called_once()
        self.cursor.close.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_importar_consulta_primero_la_ficha_completa(self):
        respuesta = self.importar()
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(self.consultar.call_args.kwargs['params']['i'], 'tt0133093')
        inserciones = [call for call in self.cursor.execute.call_args_list if 'INSERT INTO pelicula' in call.args[0]]
        self.assertEqual(len(inserciones), 1)
        self.assertEqual(inserciones[0].args[1][0], 'tt0133093')
        self.assertEqual(inserciones[0].args[1][3], '/static/img/default.svg')

    def test_reimportar_actualiza_sin_insertar(self):
        self.cursor.fetchone.side_effect = [
            {'id_pelicula': 37}, {'id_pelicula': 37, 'duracion_minutos': 136}, {'id_pelicula': 37},
        ]
        respuesta = self.importar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json['accion'], 'actualizada')
        self.assertFalse(any('INSERT INTO pelicula' in call.args[0] for call in self.cursor.execute.call_args_list))

    def test_reimportar_no_cambia_duracion_con_funciones_programadas(self):
        self.cursor.fetchone.side_effect = [
            {'id_pelicula': 37}, {'id_pelicula': 37, 'duracion_minutos': 120}, {'id_funcion': 4},
        ]
        respuesta = self.importar()
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn('duración', respuesta.json['error'])
        self.conexion.rollback.assert_called_once()
        self.conexion.commit.assert_not_called()
        self.assertFalse(any('UPDATE pelicula' in call.args[0] for call in self.cursor.execute.call_args_list))

    def test_sin_clave_informa_servicio_no_configurado(self):
        with patch.dict(os.environ, {'OMDB_API_KEY': ''}):
            respuesta = self.client.get('/api/pelicula?titulo=Matrix')
        self.assertEqual(respuesta.status_code, 503)
        self.consultar.assert_not_called()

    def test_timeout_es_504(self):
        self.consultar.side_effect = omdb_service.requests.exceptions.Timeout()
        self.assertEqual(self.client.get('/api/pelicula?titulo=Matrix').status_code, 504)

    def test_error_http_del_proveedor_es_502(self):
        self.respuesta.raise_for_status.side_effect = omdb_service.requests.exceptions.HTTPError()
        self.assertEqual(self.client.get('/api/pelicula?titulo=Matrix').status_code, 502)

    def test_pelicula_no_encontrada_es_404(self):
        self.respuesta.json.return_value = {'Response': 'False', 'Error': 'Movie not found!'}
        self.assertEqual(self.client.get('/api/pelicula?titulo=Matrix').status_code, 404)

    def test_respuesta_invalida_del_proveedor_es_502(self):
        self.respuesta.json.return_value = []
        self.assertEqual(self.client.get('/api/pelicula?titulo=Matrix').status_code, 502)

    def test_duracion_desconocida_no_se_guarda(self):
        self.ficha['Runtime'] = 'N/A'
        self.assertEqual(self.importar().status_code, 422)
        self.cursor.execute.assert_not_called()

    def test_datos_que_exceden_el_esquema_no_llegan_a_mysql(self):
        self.ficha['Genre'] = 'a' * 51
        respuesta = self.importar()
        self.assertEqual(respuesta.status_code, 422)
        self.assertIn('genero', respuesta.json['error'])
        self.cursor.execute.assert_not_called()

    def test_identificador_invalido_no_consulta_proveedor(self):
        respuesta = self.client.post('/api/peliculas/omdb/importar', json={'imdb_id': 'incorrecto'})
        self.assertEqual(respuesta.status_code, 400)
        self.consultar.assert_not_called()

    def test_cliente_no_puede_importar(self):
        self.identidad.cursor.return_value.__enter__.return_value.fetchone.return_value['rol'] = 'cliente'
        self.assertEqual(self.importar().status_code, 403)
        self.consultar.assert_not_called()

    def test_sin_token_no_puede_importar(self):
        self.client.environ_base.pop('HTTP_AUTHORIZATION')
        self.assertEqual(self.importar().status_code, 401)
        self.consultar.assert_not_called()


if __name__ == '__main__':
    unittest.main()
