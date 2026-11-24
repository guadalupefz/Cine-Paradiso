import unittest
from unittest.mock import MagicMock, patch

from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
    ESTADO_COMPRA_RECHAZADA,
)
from backend.src.services import reservas_service


class EstadosReservaTest(unittest.TestCase):
    def setUp(self):
        self.cursor = MagicMock()
        self.compra_pendiente = {
            "id_compra": 31,
            "estado": ESTADO_COMPRA_PENDIENTE,
        }

    def test_rechazar_reserva_pendiente_actualiza_estado_y_libera_entradas(self):
        with patch.object(
            reservas_service,
            "obtener_compra_reserva_para_actualizar",
            return_value=self.compra_pendiente,
        ), patch.object(
            reservas_service, "reserva_vencida", return_value=False
        ), patch.object(
            reservas_service, "actualizar_estado_compra"
        ) as actualizar, patch.object(
            reservas_service, "liberar_entradas_reserva"
        ) as liberar:
            reserva, error = reservas_service.rechazar_reserva_pendiente(
                self.cursor, 31, 8
            )

        self.assertIsNone(error)
        self.assertEqual(reserva["estado"], ESTADO_COMPRA_RECHAZADA)
        actualizar.assert_called_once_with(
            self.cursor, 31, ESTADO_COMPRA_RECHAZADA
        )
        liberar.assert_called_once_with(self.cursor, 31)

    def test_abandonar_reserva_pendiente_actualiza_estado_y_libera_entradas(self):
        with patch.object(
            reservas_service,
            "obtener_compra_reserva_para_actualizar",
            return_value=self.compra_pendiente,
        ), patch.object(
            reservas_service, "reserva_vencida", return_value=False
        ), patch.object(
            reservas_service, "actualizar_estado_compra"
        ) as actualizar, patch.object(
            reservas_service, "liberar_entradas_reserva"
        ) as liberar:
            reserva, error = reservas_service.abandonar_reserva_pendiente(
                self.cursor, 31, 8
            )

        self.assertIsNone(error)
        self.assertEqual(reserva["estado"], ESTADO_COMPRA_CANCELADA)
        actualizar.assert_called_once_with(
            self.cursor, 31, ESTADO_COMPRA_CANCELADA
        )
        liberar.assert_called_once_with(self.cursor, 31)

    def test_no_puede_modificar_reserva_de_otro_usuario(self):
        with patch.object(
            reservas_service,
            "obtener_compra_reserva_para_actualizar",
            return_value=None,
        ), patch.object(
            reservas_service, "actualizar_estado_compra"
        ) as actualizar, patch.object(
            reservas_service, "liberar_entradas_reserva"
        ) as liberar:
            reserva, error = reservas_service.rechazar_reserva_pendiente(
                self.cursor, 31, 99
            )

        self.assertIsNone(reserva)
        self.assertEqual(error["error"], "RESERVA_NO_ENCONTRADA")
        actualizar.assert_not_called()
        liberar.assert_not_called()

    def test_abandonar_reserva_vencida_registra_expiracion(self):
        with patch.object(
            reservas_service,
            "obtener_compra_reserva_para_actualizar",
            return_value=self.compra_pendiente,
        ), patch.object(
            reservas_service, "reserva_vencida", return_value=True
        ), patch.object(
            reservas_service, "actualizar_estado_compra"
        ) as actualizar, patch.object(
            reservas_service, "liberar_entradas_reserva"
        ) as liberar:
            reserva, error = reservas_service.abandonar_reserva_pendiente(
                self.cursor, 31, 8
            )

        self.assertIsNone(reserva)
        self.assertEqual(error["error"], "RESERVA_EXPIRADA")
        actualizar.assert_called_once_with(
            self.cursor, 31, ESTADO_COMPRA_EXPIRADA
        )
        liberar.assert_called_once_with(self.cursor, 31)


if __name__ == "__main__":
    unittest.main(verbosity=2)
