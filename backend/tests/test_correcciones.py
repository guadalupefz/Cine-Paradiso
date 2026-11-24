import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-verificar-jwt-de-mas-de-32-caracteres")
from flask_jwt_extended import create_access_token
from backend.app import app
from backend.autenticacion import jwt
from backend import seguridad
from backend.src.routes import servicios_routes
from backend.src.validators.duracion_validator import minutos_de_duracion
from backend.src.validators.reservas_validator import validar_datos_reserva
from backend.src.services import peliculas_service, reservas_service
from mysql.connector import Error


class Correcciones(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        bloqueo = patch.object(jwt, "_token_in_blocklist_callback", return_value=False)
        bloqueo.start()
        self.addCleanup(bloqueo.stop)

    def token(self, identidad="8", **argumentos):
        with app.app_context():
            return create_access_token(identity=identidad, **argumentos)

    def test_jwt_expirado_401(self):
        token = self.token(expires_delta=timedelta(seconds=-1))
        respuesta = self.client.get("/api/compras", headers={"Authorization": "Bearer " + token})
        self.assertEqual(respuesta.status_code, 401)

    def test_jwt_alterado_401(self):
        token = self.token()
        partes = token.split(".")
        partes[2] = ("A" if partes[2][0] != "A" else "B") + partes[2][1:]
        respuesta = self.client.get("/api/compras", headers={"Authorization": "Bearer " + ".".join(partes)})
        self.assertEqual(respuesta.status_code, 401)

    def test_cookie_vieja_no_reemplaza_jwt(self):
        with self.client.session_transaction() as sesion:
            sesion["id_usuario"] = 8
        self.assertEqual(self.client.get("/api/compras").status_code, 401)

    def test_rol_del_token_no_reemplaza_rol_en_db(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {"id_usuario": 8, "rol": "cliente"}
        token = self.token(additional_claims={"rol": "administrador"})
        with patch.object(seguridad, "get_connection", return_value=conexion), patch.object(servicios_routes, "get_connection") as escribir:
            respuesta = self.client.post("/api/servicios", json={"nombre": "Agua", "precio": "2.00"}, headers={"Authorization": "Bearer " + token})
        self.assertEqual(respuesta.status_code, 403)
        escribir.assert_not_called()

    def test_token_revocado_401(self):
        with patch.object(jwt, "_token_in_blocklist_callback", return_value=True):
            respuesta = self.client.get("/api/compras", headers={"Authorization": "Bearer " + self.token()})
        self.assertEqual(respuesta.status_code, 401)

    def test_duracion_antigua_y_nueva(self):
        for valor in (108, "108", "108 min", " 108 MIN "):
            with self.subTest(valor=valor):
                self.assertEqual(minutos_de_duracion(valor), 108)

    def test_duracion_invalida(self):
        for valor in (True, None, "N/A", "2 horas", "0", -1, "1500 min"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                minutos_de_duracion(valor)

    def test_reserva_ids_no_hashables_retorna_errores(self):
        for butacas in ([[1]], [{"id": 1}], [True], [None], [1, 1]):
            with self.subTest(butacas=butacas):
                self.assertTrue(validar_datos_reserva(1, {"butacas": butacas}))

    def test_reserva_butaca_ajena_no_escribe(self):
        cursor = MagicMock()
        with patch.object(reservas_service, "obtener_funcion", return_value={"precio_base": 8000, "fecha_hora_inicio": datetime(2032, 1, 1)}), patch.object(reservas_service, "obtener_hora_actual", return_value=datetime(2026, 11, 3)), patch.object(reservas_service, "obtener_butacas_de_funcion", return_value=[{"id_butaca": 1}]), patch.object(reservas_service, "crear_compra_pendiente") as crear:
            reserva, error = reservas_service.crear_reserva(cursor, 8, 1, [99])
        self.assertIsNone(reserva)
        self.assertEqual(error["status_code"], 400)
        crear.assert_not_called()

    def test_error_de_base_de_datos_se_propaga_al_limite_de_ruta(self):
        cursor = MagicMock()
        with patch.object(
            reservas_service,
            "obtener_funcion",
            side_effect=Error("interbloqueo simulado", errno=1213),
        ), self.assertRaises(Error):
            reservas_service.crear_reserva(cursor, 8, 1, [1])

    def test_editar_duracion_con_funciones_rechaza_y_no_confirma(self):
        datos = {"titulo": "Prueba", "sinopsis": "Prueba", "poster": "/static/img/default.svg", "duracion_minutos": 360, "clasificacion": "ATP", "genero": "Drama"}
        cursor = MagicMock()

        with patch.object(
            peliculas_service, "buscar_pelicula_por_id",
            return_value={"id_pelicula": 1, "duracion_minutos": "108 min"},
        ), patch.object(
            peliculas_service, "buscar_pelicula_por_titulo", return_value=None
        ), patch.object(
            peliculas_service, "obtener_funcion_de_pelicula",
            return_value={"id_funcion": 15},
        ), patch.object(
            peliculas_service, "editar_pelicula"
        ) as editar:
            resultado = peliculas_service.editar_pelicula_service(cursor, 1, datos)

        self.assertEqual(resultado["status"], 409)
        editar.assert_not_called()

    def test_reparar_duracion_antigua_invalida_sin_funciones(self):
        datos = {"titulo": "Prueba", "sinopsis": "Prueba", "poster": "/static/img/default.svg", "duracion_minutos": 108, "clasificacion": "ATP", "genero": "Drama"}
        cursor = MagicMock()

        with patch.object(
            peliculas_service, "buscar_pelicula_por_id",
            return_value={"id_pelicula": 1, "duracion_minutos": "N/A"},
        ), patch.object(
            peliculas_service, "buscar_pelicula_por_titulo", return_value=None
        ), patch.object(
            peliculas_service, "obtener_funcion_de_pelicula", return_value=None
        ), patch.object(
            peliculas_service, "editar_pelicula"
        ) as editar:
            resultado = peliculas_service.editar_pelicula_service(cursor, 1, datos)

        self.assertEqual(resultado["status"], 200)
        editar.assert_called_once_with(cursor, 1, datos)


if __name__ == "__main__":
    unittest.main()
