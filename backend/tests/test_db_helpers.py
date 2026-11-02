import unittest
from unittest.mock import MagicMock, patch
from mysql.connector import Error, IntegrityError
from backend import db


class AyudantesSQL(unittest.TestCase):
    def conexion(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.__enter__.return_value = cursor
        cursor.__exit__.side_effect = lambda *args: (cursor.close(), False)[1]
        parche = patch.object(db, "get_connection", return_value=conexion)
        parche.start()
        self.addCleanup(parche.stop)
        return conexion, cursor

    def test_buscar_uno_con_datos_y_parametros(self):
        conexion, cursor = self.conexion()
        cursor.fetchone.return_value = {"id": 8}
        resultado = db.ejecutar_buscar_uno("SELECT id FROM tabla WHERE id = %s", (8,))
        self.assertTrue(resultado["exito"])
        self.assertEqual(resultado["datos"], {"id": 8})
        self.assertIn("mensaje", resultado)
        conexion.cursor.assert_called_once_with(dictionary=True, buffered=True)
        cursor.execute.assert_called_once_with("SELECT id FROM tabla WHERE id = %s", (8,))
        cursor.close.assert_called_once()
        conexion.close.assert_called_once()

    def test_buscar_uno_sin_datos_es_exito(self):
        conexion, cursor = self.conexion()
        cursor.fetchone.return_value = None
        resultado = db.ejecutar_buscar_uno("SELECT id FROM tabla")
        self.assertTrue(resultado["exito"])
        self.assertIsNone(resultado["datos"])
        conexion.close.assert_called_once()

    def test_buscar_uno_error_consulta_cierra(self):
        conexion, cursor = self.conexion()
        cursor.execute.side_effect = Error("detalle interno ficticio")
        resultado = db.ejecutar_buscar_uno("SELECT id FROM tabla")
        self.assertFalse(resultado["exito"])
        self.assertIsNone(resultado["datos"])
        self.assertNotIn("detalle interno", resultado["mensaje"])
        cursor.close.assert_called_once()
        conexion.close.assert_called_once()

    def test_buscar_uno_error_conexion_controlado(self):
        with patch.object(db, "get_connection", side_effect=Error("fallo ficticio")):
            resultado = db.ejecutar_buscar_uno("SELECT 1")
        self.assertFalse(resultado["exito"])
        self.assertIsNone(resultado["datos"])

    def test_buscar_lista_conserva_contrato(self):
        conexion, cursor = self.conexion()
        cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
        resultado = db.ejecutar_buscar("SELECT id FROM tabla")
        self.assertEqual(resultado["datos"], [{"id": 1}, {"id": 2}])
        self.assertTrue(resultado["exito"])
        self.assertIn("2 registros", resultado["mensaje"])
        conexion.close.assert_called_once()

    def test_guardar_conserva_id_y_mensaje(self):
        conexion, cursor = self.conexion()
        cursor.lastrowid = 5
        resultado = db.ejecutar_guardar("INSERT INTO tabla (dato) VALUES (%s)", ("prueba",))
        self.assertEqual(resultado["id"], 5)
        self.assertTrue(resultado["exito"])
        self.assertIn("mensaje", resultado)
        conexion.commit.assert_called_once()
        conexion.rollback.assert_not_called()
        conexion.close.assert_called_once()

    def test_guardar_error_revierte_antes_de_cerrar(self):
        conexion, cursor = self.conexion()
        cursor.execute.side_effect = IntegrityError("restriccion ficticia")
        resultado = db.ejecutar_guardar("INSERT INTO tabla VALUES (%s)", (1,))
        self.assertFalse(resultado["exito"])
        conexion.rollback.assert_called_once()
        conexion.commit.assert_not_called()
        conexion.close.assert_called_once()

    def test_guardar_error_commit_revierte(self):
        conexion, cursor = self.conexion()
        conexion.commit.side_effect = Error("commit ficticio")
        resultado = db.ejecutar_guardar("INSERT INTO tabla VALUES (%s)", (1,))
        self.assertFalse(resultado["exito"])
        conexion.rollback.assert_called_once()
        conexion.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
