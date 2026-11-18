import unittest
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token

from backend import seguridad
from backend.app import app
from backend.autenticacion import jwt
from backend.src.routes import estadisticas_routes
from backend.src.services import estadisticas_service
from backend.src.validators.estadisticas_validator import validar_filtros_estadisticas


class RutasEstadisticasTest(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="clave-de-prueba-estadisticas-123456",
            JWT_SECRET_KEY="clave-de-prueba-estadisticas-123456",
        )
        self.client = app.test_client()
        self.usuario = {"id_usuario": 8, "rol": "administrador"}
        self.conexion_seguridad = MagicMock()
        cursor = self.conexion_seguridad.cursor.return_value
        cursor.__enter__.return_value = cursor
        cursor.fetchone.return_value = self.usuario

        parche_seguridad = patch.object(
            seguridad,
            "get_connection",
            return_value=self.conexion_seguridad,
        )
        parche_seguridad.start()
        self.addCleanup(parche_seguridad.stop)

        parche_blocklist = patch.object(
            jwt, "_token_in_blocklist_callback", return_value=False
        )
        parche_blocklist.start()
        self.addCleanup(parche_blocklist.stop)

        with app.app_context():
            token = create_access_token(identity="8")
        self.client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def test_consultar_ventas_delega_al_servicio_con_cursor(self):
        resultado = {
            "ventas_por_genero": [{"genero": "Drama", "entradas_vendidas": 5}],
            "ventas_por_franja_horaria": [],
            "cantidad_cancelaciones": 2,
            "filtros": {
                "desde": "2026-11-01",
                "hasta": "2026-11-15",
                "id_local": 3,
            },
        }
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.__enter__.return_value = cursor

        with patch.object(
            estadisticas_routes, "get_connection", return_value=conexion
        ), patch.object(
            estadisticas_routes,
            "consultar_ventas_service",
            return_value=resultado,
        ) as consultar:
            respuesta = self.client.get(
                "/api/estadisticas/ventas",
                query_string={
                    "desde": "2026-11-01",
                    "hasta": "2026-11-15",
                    "id_local": "3",
                },
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, resultado)
        consultar.assert_called_once_with(
            cursor, "2026-11-01", "2026-11-15", 3
        )
        conexion.close.assert_called_once()

    def test_consultar_ocupacion_delega_al_servicio_con_cursor(self):
        resultado = {
            "ocupacion_por_funcion": [],
            "ocupacion_por_pelicula": [],
            "filtros": {
                "desde": None,
                "hasta": None,
                "id_local": None,
            },
        }
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.__enter__.return_value = cursor

        with patch.object(
            estadisticas_routes, "get_connection", return_value=conexion
        ), patch.object(
            estadisticas_routes,
            "consultar_ocupacion_service",
            return_value=resultado,
        ) as consultar:
            respuesta = self.client.get("/api/estadisticas/ocupacion")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, resultado)
        consultar.assert_called_once_with(cursor, None, None, None)
        conexion.close.assert_called_once()

    def test_filtros_invalidos_no_abren_conexion(self):
        with patch.object(estadisticas_routes, "get_connection") as abrir:
            respuesta = self.client.get(
                "/api/estadisticas/ventas",
                query_string={"desde": "fecha-invalida"},
            )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json["error"], "FILTRO_INVALIDO")
        abrir.assert_not_called()

    def test_error_de_base_de_datos_devuelve_500_y_cierra_conexion(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.__enter__.return_value = cursor

        with patch.object(
            estadisticas_routes, "get_connection", return_value=conexion
        ), patch.object(
            estadisticas_routes,
            "consultar_ventas_service",
            side_effect=estadisticas_routes.mysql.connector.Error("Error SQL"),
        ):
            respuesta = self.client.get("/api/estadisticas/ventas")

        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json["error"], "ERROR_BASE_DATOS")
        conexion.close.assert_called_once()

    def test_error_interno_devuelve_500_y_cierra_conexion(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.__enter__.return_value = cursor

        with patch.object(
            estadisticas_routes, "get_connection", return_value=conexion
        ), patch.object(
            estadisticas_routes,
            "consultar_ocupacion_service",
            side_effect=Exception("Error interno"),
        ):
            respuesta = self.client.get("/api/estadisticas/ocupacion")

        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(respuesta.json["error"], "ERROR_SERVIDOR")
        conexion.close.assert_called_once()


class ServicioEstadisticasTest(unittest.TestCase):
    def test_consultar_ventas_obtiene_todos_los_datos(self):
        cursor = MagicMock()
        por_genero = [{"genero": "Drama", "entradas_vendidas": 5}]
        por_franja = [{"franja_horaria": "Noche", "entradas_vendidas": 5}]
        cancelaciones = {"cantidad_cancelaciones": 2}

        with patch.object(
            estadisticas_service.repo,
            "obtener_ventas_por_genero",
            return_value=por_genero,
        ) as genero, patch.object(
            estadisticas_service.repo,
            "obtener_ventas_por_franja",
            return_value=por_franja,
        ) as franja, patch.object(
            estadisticas_service.repo,
            "obtener_cantidad_cancelaciones",
            return_value=cancelaciones,
        ) as canceladas:
            resultado = estadisticas_service.consultar_ventas_service(
                cursor, "2026-11-01", "2026-11-15", 3
            )

        self.assertEqual(resultado["ventas_por_genero"], por_genero)
        self.assertEqual(resultado["ventas_por_franja_horaria"], por_franja)
        self.assertEqual(resultado["cantidad_cancelaciones"], 2)
        self.assertEqual(
            resultado["filtros"],
            {
                "desde": "2026-11-01",
                "hasta": "2026-11-15",
                "id_local": 3,
            },
        )
        genero.assert_called_once_with(
            cursor, "2026-11-01", "2026-11-15", 3
        )
        franja.assert_called_once_with(
            cursor, "2026-11-01", "2026-11-15", 3
        )
        canceladas.assert_called_once_with(
            cursor, "2026-11-01", "2026-11-15", 3
        )

    def test_consultar_ventas_con_resultados_vacios(self):
        cursor = MagicMock()

        with patch.object(
            estadisticas_service.repo,
            "obtener_ventas_por_genero",
            return_value=None,
        ), patch.object(
            estadisticas_service.repo,
            "obtener_ventas_por_franja",
            return_value=[],
        ), patch.object(
            estadisticas_service.repo,
            "obtener_cantidad_cancelaciones",
            return_value={"cantidad_cancelaciones": 0},
        ):
            resultado = estadisticas_service.consultar_ventas_service(cursor)

        self.assertEqual(resultado["ventas_por_genero"], [])
        self.assertEqual(resultado["ventas_por_franja_horaria"], [])
        self.assertEqual(resultado["cantidad_cancelaciones"], 0)

    def test_consultar_ocupacion_obtiene_datos_por_funcion_y_pelicula(self):
        cursor = MagicMock()
        por_funcion = [{"id_funcion": 1, "porcentaje_ocupacion": 50}]
        por_pelicula = [{"id_pelicula": 2, "porcentaje_ocupacion": 50}]

        with patch.object(
            estadisticas_service.repo,
            "obtener_ocupacion_por_funcion",
            return_value=por_funcion,
        ) as funcion, patch.object(
            estadisticas_service.repo,
            "obtener_ocupacion_por_pelicula",
            return_value=por_pelicula,
        ) as pelicula:
            resultado = estadisticas_service.consultar_ocupacion_service(
                cursor, "2026-11-01", "2026-11-15", 3
            )

        self.assertEqual(resultado["ocupacion_por_funcion"], por_funcion)
        self.assertEqual(resultado["ocupacion_por_pelicula"], por_pelicula)
        self.assertEqual(
            resultado["filtros"],
            {
                "desde": "2026-11-01",
                "hasta": "2026-11-15",
                "id_local": 3,
            },
        )
        funcion.assert_called_once_with(
            cursor, "2026-11-01", "2026-11-15", 3
        )
        pelicula.assert_called_once_with(
            cursor, "2026-11-01", "2026-11-15", 3
        )

    def test_consultar_ocupacion_con_resultados_vacios(self):
        cursor = MagicMock()

        with patch.object(
            estadisticas_service.repo,
            "obtener_ocupacion_por_funcion",
            return_value=None,
        ), patch.object(
            estadisticas_service.repo,
            "obtener_ocupacion_por_pelicula",
            return_value=[],
        ):
            resultado = estadisticas_service.consultar_ocupacion_service(cursor)

        self.assertEqual(resultado["ocupacion_por_funcion"], [])
        self.assertEqual(resultado["ocupacion_por_pelicula"], [])


class ValidatorEstadisticasTest(unittest.TestCase):
    def test_filtros_validos(self):
        desde, hasta, id_local, error = validar_filtros_estadisticas({
            "desde": "2026-11-01",
            "hasta": "2026-11-15",
            "id_local": "3",
        })

        self.assertEqual(desde, "2026-11-01")
        self.assertEqual(hasta, "2026-11-15")
        self.assertEqual(id_local, 3)
        self.assertIsNone(error)

    def test_id_local_no_entero(self):
        resultado = validar_filtros_estadisticas({"id_local": "abc"})

        self.assertEqual(
            resultado[3],
            "El ID del local debe ser un número entero.",
        )

    def test_id_local_no_positivo(self):
        resultado = validar_filtros_estadisticas({"id_local": "0"})

        self.assertEqual(
            resultado[3],
            "El ID del local debe ser positivo.",
        )

    def test_fecha_con_formato_invalido(self):
        resultado = validar_filtros_estadisticas({"desde": "15-11-2026"})

        self.assertEqual(
            resultado[3],
            "Las fechas deben tener formato AAAA-MM-DD.",
        )

    def test_fecha_desde_posterior_a_hasta(self):
        resultado = validar_filtros_estadisticas({
            "desde": "2026-11-20",
            "hasta": "2026-11-10",
        })

        self.assertEqual(
            resultado[3],
            "La fecha desde no puede ser posterior a hasta.",
        )


if __name__ == "__main__":
    unittest.main()
