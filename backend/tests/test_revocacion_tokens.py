from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import unittest

from mysql.connector import Error, IntegrityError
from backend import autenticacion
from backend.src.repositories.tokens_repository import guardar_token_revocado


class RevocacionTokens(unittest.TestCase):
    def setUp(self):
        self.conexion=MagicMock()
        self.cursor=self.conexion.cursor.return_value.__enter__.return_value
        self.parche=patch.object(autenticacion,'get_connection',return_value=self.conexion)
        self.parche.start()
        self.addCleanup(self.parche.stop)
        self.datos={'jti':'identificador-de-prueba','exp':int(datetime(2030,1,1,tzinfo=timezone.utc).timestamp())}

    def test_insert_normal_parametrizado(self):
        guardar_token_revocado(self.cursor,self.datos['jti'],datetime(2030,1,1))
        consulta,parametros=self.cursor.execute.call_args.args
        self.assertNotIn('IGNORE',consulta)
        self.assertEqual(parametros,(self.datos['jti'],datetime(2030,1,1)))

    def test_token_duplicado_se_acepta_sin_ocultar_otros_errores(self):
        def ejecutar(consulta,parametros=None):
            if consulta.startswith('INSERT'):
                raise IntegrityError('duplicado',errno=1062)
        self.cursor.execute.side_effect=ejecutar
        autenticacion.revocar_token(self.datos)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()
        self.conexion.close.assert_called_once()

    def test_otro_error_de_integridad_se_propaga_y_revierte(self):
        self.cursor.execute.side_effect=IntegrityError('dato inválido',errno=1048)
        with self.assertRaises(IntegrityError):
            autenticacion.revocar_token(self.datos)
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_error_al_confirmar_revierte_y_cierra(self):
        self.conexion.commit.side_effect=Error('falló commit')
        with self.assertRaises(Error):
            autenticacion.revocar_token(self.datos)
        self.conexion.rollback.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_vencimiento_se_conserva_en_utc_para_mysql(self):
        self.assertEqual(autenticacion.vencimiento_utc(self.datos),datetime(2030,1,1))

    def test_consulta_token_revocado_y_cierra(self):
        self.cursor.fetchone.return_value=('identificador-de-prueba',)
        self.assertTrue(autenticacion.token_revocado({},self.datos))
        self.conexion.close.assert_called_once()

    def test_error_de_consulta_no_concede_acceso(self):
        self.cursor.execute.side_effect=Error('falló SELECT')
        with self.assertRaises(Error):
            autenticacion.token_revocado({},self.datos)
        self.conexion.close.assert_called_once()


if __name__=='__main__':
    unittest.main()
