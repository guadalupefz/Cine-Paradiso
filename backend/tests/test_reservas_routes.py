import unittest
from unittest.mock import MagicMock, patch

from mysql.connector import Error

from backend.src.routes import reservas_routes


class TransaccionesReservasTest(unittest.TestCase):
    def setUp(self):
        self.conexion = MagicMock()
        self.cursor = self.conexion.cursor.return_value
        self.cursor.__enter__.return_value = self.cursor

    def _procesar(self, operacion):
        with patch.object(
            reservas_routes, "get_connection", return_value=self.conexion
        ):
            return reservas_routes._procesar_transaccion_reserva(
                operacion, "Error de prueba."
            )

    def test_operacion_exitosa_confirma_y_cierra(self):
        resultado = {"id_compra": 31}

        reserva, error = self._procesar(lambda cursor: (resultado, None))

        self.assertEqual(reserva, resultado)
        self.assertIsNone(error)
        self.conexion.start_transaction.assert_called_once()
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()
        self.conexion.close.assert_called_once()

    def test_error_de_regla_revierte(self):
        error_regla = {
            "error": "BUTACAS_OCUPADAS",
            "mensaje": "Butaca ocupada.",
            "status_code": 409,
        }

        reserva, error = self._procesar(lambda cursor: (None, error_regla))

        self.assertIsNone(reserva)
        self.assertIs(error, error_regla)
        self.conexion.rollback.assert_called_once()
        self.conexion.commit.assert_not_called()
        self.conexion.close.assert_called_once()

    def test_reserva_expirada_confirma_actualizacion_de_estado(self):
        error_expirada = {
            "error": "RESERVA_EXPIRADA",
            "mensaje": "La reserva ya venció.",
            "status_code": 409,
        }

        reserva, error = self._procesar(
            lambda cursor: (None, error_expirada)
        )

        self.assertIsNone(reserva)
        self.assertEqual(error["status_code"], 409)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()

    def test_error_de_base_de_datos_revierte_y_mapea_interbloqueo(self):
        def fallar(cursor):
            raise Error("interbloqueo simulado", errno=1213)

        reserva, error = self._procesar(fallar)

        self.assertIsNone(reserva)
        self.assertEqual(error["error"], "CONFLICTO_RESERVA")
        self.assertEqual(error["status_code"], 409)
        self.conexion.rollback.assert_called_once()
        self.conexion.commit.assert_not_called()
        self.conexion.close.assert_called_once()

    def test_error_duplicado_ajeno_a_butacas_no_se_mapea_como_conflicto(self):
        def fallar(cursor):
            raise Error("clave duplicada", errno=1062)

        reserva, error = self._procesar(fallar)

        self.assertIsNone(reserva)
        self.assertEqual(error["error"], "ERROR_BASE_DATOS")
        self.assertEqual(error["status_code"], 500)

    def test_error_duplicado_de_butaca_se_mapea_como_conflicto(self):
        def fallar(cursor):
            raise Error("uq_entrada_ocupacion_activa", errno=1062)

        reserva, error = self._procesar(fallar)

        self.assertIsNone(reserva)
        self.assertEqual(error["error"], "BUTACAS_OCUPADAS")
        self.assertEqual(error["status_code"], 409)


if __name__ == "__main__":
    unittest.main(verbosity=2)
