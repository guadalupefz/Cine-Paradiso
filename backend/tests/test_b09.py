import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-backend-2026")

from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_CONFIRMADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
    ESTADO_COMPRA_RECHAZADA,
    ESTADOS_COMPRA_VALIDOS,
    RESERVA_DURACION_MINUTOS,
)
from backend.src.services import reservas_service


class ContratoNovB09Test(unittest.TestCase):
    def setUp(self):
        self.creacion = datetime(2026, 11, 9, 18, 30, 0)
        self.conexion = MagicMock()
        self.parches = [
            patch.object(reservas_service, "get_connection", return_value=self.conexion),
            patch.object(
                reservas_service,
                "obtener_funcion",
                return_value={
                    "id_funcion": 12,
                    "precio_base": "8000.00",
                    "fecha_hora_inicio": self.creacion + timedelta(hours=1),
                },
            ),
            patch.object(reservas_service, "obtener_hora_actual", return_value=self.creacion),
            patch.object(
                reservas_service,
                "obtener_butacas_de_funcion",
                return_value=[{"id_butaca": 4}],
            ),
            patch.object(reservas_service, "obtener_butacas_ocupadas_con_bloqueo", return_value=[]),
            patch.object(reservas_service, "limpiar_reservas_expiradas"),
            patch.object(reservas_service, "crear_compra_pendiente", return_value=31),
            patch.object(reservas_service, "crear_entradas_reserva"),
        ]
        self.mocks = [parche.start() for parche in self.parches]
        self.addCleanup(self._detener_parches)

    def _detener_parches(self):
        for parche in reversed(self.parches):
            parche.stop()

    def test_reserva_expira_exactamente_quince_minutos_desde_su_creacion(self):
        reserva, error = reservas_service.crear_reserva(8, 12, [4])

        self.assertIsNone(error)
        self.assertEqual(
            self.mocks[6].call_args.args[3],
            self.creacion,
            "La fecha de creación usada al insertar debe ser la base del vencimiento.",
        )
        vencimiento = datetime.strptime(
            reserva["fecha_hora_vencimiento"], "%Y-%m-%d %H:%M:%S"
        )
        self.assertEqual(
            vencimiento - self.creacion,
            timedelta(minutes=RESERVA_DURACION_MINUTOS),
        )
        self.assertEqual(RESERVA_DURACION_MINUTOS, 15)
        self.assertEqual(reserva["estado"], ESTADO_COMPRA_PENDIENTE)

    def test_estados_de_compra_estan_centralizados_y_sin_valores_legacy(self):
        self.assertEqual(
            ESTADOS_COMPRA_VALIDOS,
            frozenset(
                {
                    ESTADO_COMPRA_PENDIENTE,
                    ESTADO_COMPRA_CONFIRMADA,
                    ESTADO_COMPRA_EXPIRADA,
                    ESTADO_COMPRA_CANCELADA,
                    ESTADO_COMPRA_RECHAZADA,
                }
            ),
        )
        self.assertNotIn("aprobada", ESTADOS_COMPRA_VALIDOS)

    def test_edicion_parametriza_estado_y_compra_en_el_orden_del_sql(self):
        cursor = self.conexion.cursor.return_value.__enter__.return_value
        cursor.fetchone.side_effect = [
            {"id_compra": 31, "estado": ESTADO_COMPRA_PENDIENTE},
            {"vencida": False},
            {"id_funcion": 12},
        ]
        cursor.fetchall.return_value = []

        reserva, error = reservas_service.editar_reserva_pendiente(31, 8, [4])

        self.assertIsNone(error)
        self.assertEqual(reserva["estado"], ESTADO_COMPRA_PENDIENTE)
        consulta_butacas = next(
            llamada
            for llamada in cursor.execute.call_args_list
            if "entrada.id_compra <> %s" in llamada.args[0]
        )
        self.assertEqual(
            consulta_butacas.args[1],
            [
                12,
                4,
                31,
                ESTADO_COMPRA_CONFIRMADA,
                ESTADO_COMPRA_PENDIENTE,
                RESERVA_DURACION_MINUTOS,
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
