import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock, patch

from flask import Flask

from backend.seguridad import crear_limitador
from backend.src.routes.auth_routes import auth_bp


class LimitadorSolicitudes(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='clave-de-prueba')
        self.reloj = patch('backend.seguridad.time.monotonic', return_value=0)
        self.ahora = self.reloj.start()
        self.addCleanup(self.reloj.stop)

    def ruta(self, nombre='/prueba', max_hora=2, max_dia=4):
        ejecutar = Mock(return_value=('Operación realizada', 200))
        limitar = crear_limitador()

        @self.app.post(nombre, endpoint=nombre)
        @limitar(max_hora=max_hora, max_dia=max_dia)
        def operacion():
            return ejecutar()

        return ejecutar

    def test_rechaza_exceso_antes_de_ejecutar_la_operacion(self):
        ejecutar = self.ruta()
        client = self.app.test_client()
        self.assertEqual(client.post('/prueba').status_code, 200)
        self.assertEqual(client.post('/prueba').status_code, 200)
        respuesta = client.post('/prueba')
        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(respuesta.headers['Retry-After'], '3600')
        self.assertIn('Demasiados intentos', respuesta.json['error'])
        self.assertEqual(ejecutar.call_count, 2)

    def test_las_ip_tienen_contadores_independientes(self):
        self.ruta(max_hora=1)
        client = self.app.test_client()
        self.assertEqual(client.post('/prueba', environ_overrides={'REMOTE_ADDR':'192.0.2.1'}).status_code, 200)
        self.assertEqual(client.post('/prueba', environ_overrides={'REMOTE_ADDR':'192.0.2.1'}).status_code, 429)
        self.assertEqual(client.post('/prueba', environ_overrides={'REMOTE_ADDR':'192.0.2.2'}).status_code, 200)

    def test_vuelve_a_permitir_al_cumplirse_la_hora(self):
        self.ruta(max_hora=1)
        client = self.app.test_client()
        client.post('/prueba')
        self.ahora.return_value = 3599
        respuesta = client.post('/prueba')
        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(respuesta.headers['Retry-After'], '1')
        self.ahora.return_value = 3600
        self.assertEqual(client.post('/prueba').status_code, 200)

    def test_limite_diario_acumula_intentos_de_horas_distintas(self):
        self.ruta(max_hora=2, max_dia=2)
        client = self.app.test_client()
        client.post('/prueba')
        self.ahora.return_value = 3600
        client.post('/prueba')
        self.ahora.return_value = 7200
        respuesta = client.post('/prueba')
        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(respuesta.headers['Retry-After'], '79200')

    def test_el_bloqueo_indica_la_espera_de_ambos_limites(self):
        self.ruta(max_hora=1, max_dia=1)
        client = self.app.test_client()
        client.post('/prueba')
        self.assertEqual(client.post('/prueba').headers['Retry-After'], '86400')

    def test_elimina_intentos_que_cumplieron_24_horas(self):
        self.ruta(max_hora=1, max_dia=1)
        client = self.app.test_client()
        client.post('/prueba')
        self.ahora.return_value = 86400
        self.assertEqual(client.post('/prueba').status_code, 200)
        self.assertEqual(self.app.extensions['limites_solicitudes'][('/prueba','127.0.0.1')], [86400])

    def test_login_y_registro_reales_usan_limites_independientes(self):
        self.app.register_blueprint(auth_bp, url_prefix='/api')
        client = self.app.test_client()
        with patch('backend.src.routes.auth_routes.get_connection') as abrir:
            for _ in range(50):
                self.assertEqual(client.post('/api/auth/login', json={}).status_code, 400)
            self.assertEqual(client.post('/api/auth/login', json={}).status_code, 429)
            self.assertEqual(client.post('/api/auth/registro', json={}).status_code, 400)
            abrir.assert_not_called()

    def test_las_aplicaciones_no_comparten_el_historial(self):
        self.app.register_blueprint(auth_bp, url_prefix='/api')
        otra_app = Flask('otra_aplicacion')
        otra_app.config.update(TESTING=True, SECRET_KEY='otra-clave')
        otra_app.register_blueprint(auth_bp, url_prefix='/api')
        client = self.app.test_client()
        for _ in range(50):
            client.post('/api/auth/login', json={})
        self.assertEqual(client.post('/api/auth/login', json={}).status_code, 429)
        self.assertEqual(otra_app.test_client().post('/api/auth/login', json={}).status_code, 400)

    def test_solicitudes_simultaneas_respetan_el_limite(self):
        ejecutar = self.ruta(max_hora=3)
        barrera = Barrier(8)

        def solicitar(_):
            with self.app.test_client() as client:
                barrera.wait(timeout=5)
                return client.post('/prueba').status_code

        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = list(pool.map(solicitar, range(8)))
        self.assertEqual(resultados.count(200), 3)
        self.assertEqual(resultados.count(429), 5)
        self.assertEqual(ejecutar.call_count, 3)


if __name__ == '__main__':
    unittest.main()
