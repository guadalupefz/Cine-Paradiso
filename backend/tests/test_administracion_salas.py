import unittest
from unittest.mock import MagicMock, patch

import mysql.connector
from flask_jwt_extended import create_access_token

from backend.app import app
from backend import seguridad
from backend.autenticacion import jwt
from backend.src.routes import salas_routes as salas
from backend.src.routes import configuracion_butacas as butacas
from backend.src.services import eliminacion_estructura_service as eliminacion


class TestAdministracionSalas(unittest.TestCase):

    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="clave-test")
        self.client = app.test_client()

        bloqueo = patch.object(
            jwt, "_token_in_blocklist_callback", return_value=False
        )
        bloqueo.start()
        self.addCleanup(bloqueo.stop)

        self.cn_seg = MagicMock()
        self.cur_seg = self.cn_seg.cursor.return_value
        self.cur_seg.__enter__.return_value = self.cur_seg
        self.cur_seg.fetchone.return_value = {
            "id_usuario": 8,
            "rol": "administrador",
        }

        parche_seg = patch.object(
            seguridad, "get_connection", return_value=self.cn_seg
        )
        parche_seg.start()
        self.addCleanup(parche_seg.stop)

        with app.app_context():
            token = create_access_token(identity="8")

        self.client.environ_base["HTTP_AUTHORIZATION"] = "Bearer " + token

    def base(self, modulo):
        conn = MagicMock()
        cursor = conn.cursor.return_value
        cursor.__enter__.return_value = cursor
        cursor.__exit__.return_value = False
        cursor.lastrowid = 37

        parche = patch.object(modulo, "get_connection", return_value=conn)
        parche.start()
        self.addCleanup(parche.stop)

        return conn, cursor

    def test_listar_salas_de_local(self):
        conn, cursor = self.base(salas)
        cursor.fetchone.return_value = {"id_local": 1}

        resultado = [{"id_sala": 2, "nombre": "Sala 1", "capacidad": 10}]

        with patch.object(
            salas, "obtener_salas_por_local", return_value=resultado
        ):
            respuesta = self.client.get("/api/locales/1/salas")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()["salas"], resultado)
        conn.close.assert_called_once()

    def test_listar_salas_de_local_inexistente(self):
        conn, cursor = self.base(salas)
        cursor.fetchone.return_value = None

        respuesta = self.client.get("/api/locales/99/salas")

        self.assertEqual(respuesta.status_code, 404)
        conn.close.assert_called_once()

    def test_crear_sala_correctamente(self):
        conn, cursor = self.base(salas)
        cursor.fetchone.return_value = {"id_local": 1}

        respuesta = self.client.post(
            "/api/locales/1/salas",
            json={"nombre": "Sala nueva", "capacidad": 20}
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.get_json()["id_sala"], 37)
        cursor.execute.assert_any_call(
            "INSERT INTO sala (id_local, nombre, capacidad) VALUES (%s, %s, %s)",
            (1, "Sala nueva", 20)
        )
        conn.commit.assert_called_once()

    def test_crear_sala_con_nombre_duplicado(self):
        conn, cursor = self.base(salas)
        cursor.execute.side_effect = [
            None,
            mysql.connector.IntegrityError("duplicado")
        ]
        cursor.fetchone.return_value = {"id_local": 1}

        respuesta = self.client.post(
            "/api/locales/1/salas",
            json={"nombre": "Sala existente", "capacidad": 20}
        )

        self.assertEqual(respuesta.status_code, 409)
        conn.rollback.assert_called_once()

    def test_rechazar_capacidad_invalida(self):
        respuesta = self.client.post(
            "/api/locales/1/salas",
            json={"nombre": "Sala nueva", "capacidad": 0}
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_configurar_butacas_correctamente(self):
        conn, cursor = self.base(butacas)
        cursor.fetchone.side_effect = [
            {"capacidad": 2},
            {"cantidad": 0}
        ]

        respuesta = self.client.post(
            "/api/salas/1/butacas",
            json={
                "butacas": [
                    {"fila": "A", "numero": 1},
                    {"fila": "A", "numero": 2}
                ]
            }
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.get_json()["cantidad"], 2)
        cursor.executemany.assert_called_once_with(
            "INSERT INTO butaca (id_sala, fila, numero) VALUES (%s, %s, %s)",
            [(1, "A", 1), (1, "A", 2)]
        )
        conn.commit.assert_called_once()

    def test_rechazar_cantidad_de_butacas_incorrecta(self):
        conn, cursor = self.base(butacas)
        cursor.fetchone.return_value = {"capacidad": 3}

        respuesta = self.client.post(
            "/api/salas/1/butacas",
            json={"butacas": [{"fila": "A", "numero": 1}]}
        )

        self.assertEqual(respuesta.status_code, 400)
        cursor.executemany.assert_not_called()
        conn.commit.assert_not_called()

    def test_rechazar_butacas_repetidas(self):
        respuesta = self.client.post(
            "/api/salas/1/butacas",
            json={
                "butacas": [
                    {"fila": "A", "numero": 1},
                    {"fila": "a", "numero": 1}
                ]
            }
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rechazar_sala_ya_configurada(self):
        conn, cursor = self.base(butacas)
        cursor.fetchone.side_effect = [
            {"capacidad": 2},
            {"cantidad": 2}
        ]

        respuesta = self.client.post(
            "/api/salas/1/butacas",
            json={
                "butacas": [
                    {"fila": "A", "numero": 1},
                    {"fila": "A", "numero": 2}
                ]
            }
        )

        self.assertEqual(respuesta.status_code, 409)
        cursor.executemany.assert_not_called()
        conn.commit.assert_not_called()

    def test_eliminar_local_o_sala_sin_actividad(self):
        for recurso in ("locales", "salas"):
            with self.subTest(recurso=recurso):
                conn, cursor = self.base(eliminacion)
                cursor.fetchone.side_effect = [{"id": 7}, {"en_uso": 0}]
                cursor.rowcount = 1
                respuesta = self.client.delete(f"/api/{recurso}/7")
                self.assertEqual(respuesta.status_code, 200)
                conn.commit.assert_called_once()
                conn.close.assert_called_once()
                sql = [llamada.args[0] for llamada in cursor.execute.call_args_list]
                self.assertTrue(any(consulta.startswith("DELETE") and "butaca" in consulta for consulta in sql))
                self.assertFalse(any(consulta.startswith("DELETE") and "funcion" in consulta for consulta in sql))

    def test_eliminar_rechaza_funciones_o_entradas_sin_borrar(self):
        for recurso in ("locales", "salas"):
            with self.subTest(recurso=recurso):
                conn, cursor = self.base(eliminacion)
                cursor.fetchone.side_effect = [{"id": 7}, {"en_uso": 1}]
                respuesta = self.client.delete(f"/api/{recurso}/7")
                self.assertEqual(respuesta.status_code, 409)
                self.assertFalse(any(c.args[0].startswith("DELETE") for c in cursor.execute.call_args_list))
                conn.commit.assert_not_called()
                conn.rollback.assert_called_once()
                conn.close.assert_called_once()

    def test_eliminar_inexistente_devuelve_404(self):
        for recurso in ("locales", "salas"):
            with self.subTest(recurso=recurso):
                conn, cursor = self.base(eliminacion)
                cursor.fetchone.return_value = None
                respuesta = self.client.delete(f"/api/{recurso}/99")
                self.assertEqual(respuesta.status_code, 404)
                conn.commit.assert_not_called()
                conn.close.assert_called_once()

    def test_eliminar_id_cero_no_consulta_base(self):
        with patch.object(eliminacion, "get_connection") as conectar:
            for recurso in ("locales", "salas"):
                self.assertEqual(self.client.delete(f"/api/{recurso}/0").status_code, 400)
            conectar.assert_not_called()

    def test_eliminar_revierte_ante_nueva_dependencia(self):
        for recurso in ("locales", "salas"):
            with self.subTest(recurso=recurso):
                conn, cursor = self.base(eliminacion)
                cursor.fetchone.side_effect = [{"id": 7}, {"en_uso": 0}]
                def ejecutar(sql, parametros):
                    if sql.startswith("DELETE"):
                        raise mysql.connector.IntegrityError("Hay dependencias", errno=1451)
                cursor.execute.side_effect = ejecutar
                respuesta = self.client.delete(f"/api/{recurso}/7")
                self.assertEqual(respuesta.status_code, 409)
                conn.rollback.assert_called_once()
                conn.commit.assert_not_called()
                conn.close.assert_called_once()

    def test_eliminar_revierte_si_falla_commit(self):
        conn, cursor = self.base(eliminacion)
        cursor.fetchone.side_effect = [{"id": 7}, {"en_uso": 0}]
        cursor.rowcount = 1
        conn.commit.side_effect = mysql.connector.Error("Conexión interrumpida", errno=2006)
        self.assertEqual(self.client.delete("/api/salas/7").status_code, 500)
        conn.rollback.assert_called_once()
        conn.close.assert_called_once()

    def test_eliminar_exige_administrador(self):
        with patch.object(eliminacion, "get_connection") as conectar:
            for recurso in ("locales", "salas"):
                self.assertEqual(self.client.delete(f"/api/{recurso}/7", headers={"Authorization": ""}).status_code, 401)
            self.cur_seg.fetchone.return_value = {"id_usuario": 8, "rol": "cliente"}
            for recurso in ("locales", "salas"):
                self.assertEqual(self.client.delete(f"/api/{recurso}/7").status_code, 403)
            conectar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
