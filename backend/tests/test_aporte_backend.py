"""Pruebas del aporte con Flask real y MySQL simulado: sin credenciales ni datos reales."""
import os
import sys
from pathlib import Path
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('SECRET_KEY', 'clave-ficticia-solo-para-pruebas')
from backend.app import app
from backend import seguridad
from backend.autenticacion import jwt
from flask_jwt_extended import create_access_token, decode_token
from backend.src.routes import auth_routes as auth, compras_routes as compras, servicios_routes as servicios
from mysql.connector import Error, IntegrityError
from werkzeug.security import generate_password_hash
from backend.src.repositories import auth_repository

class AporteBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hash = generate_password_hash('clave-ficticia')

    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY='clave-ficticia-del-test')
        self.client = app.test_client()
        self.revocados = set()
        bloqueo = patch.object(jwt, '_token_in_blocklist_callback', side_effect=lambda cabecera, datos: datos['jti'] in self.revocados)
        bloqueo.start()
        self.addCleanup(bloqueo.stop)
        revocar = patch.object(auth, 'revocar_token', side_effect=lambda datos: self.revocados.add(datos['jti']))
        revocar.start()
        self.addCleanup(revocar.stop)
        self.cn_seg = MagicMock()
        self.cur_seg = self.cn_seg.cursor.return_value
        self.cur_seg.__enter__.return_value = self.cur_seg
        self.cur_seg.__exit__.side_effect = lambda *args: (self.cur_seg.close(), False)[1]
        parche = patch.object(seguridad, 'get_connection', return_value=self.cn_seg)
        parche.start()
        self.addCleanup(parche.stop)

    def autenticar(self, rol='cliente', identificador=8):
        with app.app_context():
            self.token = create_access_token(identity=str(identificador))
        self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + self.token
        self.cur_seg.fetchone.return_value = {'id_usuario': identificador, 'rol': rol}

    def base(self, modulo, filas=None, fila=None):
        cn = MagicMock()
        cur = cn.cursor.return_value
        cur.__enter__.return_value = cur
        cur.__exit__.side_effect = lambda *args: (cur.close(), False)[1]
        cur.fetchall.return_value = [] if filas is None else filas
        cur.fetchone.return_value = fila
        cur.lastrowid = 37
        parche = patch.object(modulo, 'get_connection', return_value=cn)
        parche.start()
        self.addCleanup(parche.stop)
        return cn, cur

    def post_servicio(self, datos=None):
        return self.client.post(
            '/api/servicios',
            json=datos or {
                'nombre': ' Agua ',
                'descripcion': 'Agua mineral',
                'precio': '2000.00'
            }
        )

    def assertCierre(self, cn, cur):
        cur.close.assert_called_once()
        cn.close.assert_called_once()

    def test_get_servicios_publico_serializa_decimal(self):
        cn, cur = self.base(servicios, filas=[{'nombre': 'Agua', 'precio': Decimal('2000.00')}])
        r = self.client.get('/api/servicios')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json[0]['precio'], '2000.00')
        self.assertCierre(cn, cur)

    def test_alta_sin_sesion_401_no_conecta(self):
        with patch.object(servicios, 'get_connection') as abrir:
            self.assertEqual(self.post_servicio().status_code, 401)
            abrir.assert_not_called()
        self.cn_seg.cursor.assert_not_called()

    def test_cliente_no_puede_crear_ni_elegir_rol(self):
        self.autenticar(' Cliente ')
        with patch.object(servicios, 'get_connection') as abrir:
            r = self.post_servicio({'nombre': 'Agua', 'precio': '2', 'rol': 'administrador'})
            self.assertEqual(r.status_code, 403)
            abrir.assert_not_called()
        self.assertEqual(self.cur_seg.execute.call_args.args[1], (8,))
        self.assertCierre(self.cn_seg, self.cur_seg)

    def test_administrador_crea_y_confirma(self):
        self.autenticar('administrador')
        cn, cur = self.base(servicios)
        r = self.post_servicio()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json['id_servicio'], 37)
        self.assertEqual(cur.execute.call_args.args[1], ('Agua', 'Agua mineral', Decimal('2000.00'), ''))
        cn.commit.assert_called_once()
        cn.rollback.assert_not_called()
        self.assertCierre(cn, cur)

    def test_rol_actual_de_base_prevalece_sobre_sesion(self):
        self.autenticar('cliente')
        with self.client.session_transaction() as s:
            s['rol'] = 'administrador'
        self.assertEqual(self.post_servicio().status_code, 403)

    def test_usuario_eliminado_401_limpia_sesion(self):
        self.autenticar()
        self.cur_seg.fetchone.return_value = None
        self.assertEqual(self.client.get('/api/compras').status_code, 401)
        self.assertCierre(self.cn_seg, self.cur_seg)

    def test_identificador_de_sesion_invalido(self):
        for valor in [True, 8, '', 'abc', '0', '-1']:
            with self.subTest(valor=valor):
                with app.app_context():
                    token = create_access_token(identity=valor)
                self.client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + token
                self.assertEqual(self.client.get('/api/compras').status_code, 401)
        self.cn_seg.cursor.assert_not_called()

    def test_rol_desconocido_403(self):
        self.autenticar('rol-inventado')
        self.assertEqual(self.client.get('/api/compras').status_code, 403)

    def test_fallo_verificacion_permisos_500(self):
        self.autenticar()
        self.cur_seg.execute.side_effect = Error('fallo simulado')
        self.assertEqual(self.client.get('/api/compras').status_code, 500)
        self.assertCierre(self.cn_seg, self.cur_seg)

    def test_alta_datos_invalidos_400_antes_de_escribir(self):
        self.autenticar('administrador')
        datos = [[], {}, {'nombre': ' '*3, 'precio': '2'}, {'nombre': 'x'*101, 'precio': '2'}]
        datos += [{'nombre': 'Agua', 'precio': p} for p in [True, 2, None, '', 'abc', 'NaN', 'sNaN', 'Infinity', '0', '-1', '1.234', '100000000.00']]
        with patch.object(servicios, 'get_connection') as abrir:
            for cuerpo in datos:
                with self.subTest(cuerpo=cuerpo):
                    self.assertEqual(self.client.post('/api/servicios', json=cuerpo).status_code, 400)
            abrir.assert_not_called()

    def test_alta_duplicada_409_y_rollback(self):
        self.autenticar('administrador')
        cn, cur = self.base(servicios)
        cur.execute.side_effect = IntegrityError('duplicado simulado')
        self.assertEqual(self.post_servicio().status_code, 409)
        cn.rollback.assert_called_once()
        cn.commit.assert_not_called()
        self.assertCierre(cn, cur)

    def test_fallo_commit_500_revierte(self):
        self.autenticar('administrador')
        cn, cur = self.base(servicios)
        cn.commit.side_effect = Error('fallo simulado')
        self.assertEqual(self.post_servicio().status_code, 500)
        cn.rollback.assert_called_once()
        self.assertCierre(cn, cur)

    def test_login_valido_sesion_y_consulta_parametrizada(self):
        cn, cur = self.base(auth_repository, fila={'id_usuario': 8, 'password_hash': self.hash, 'rol': 'cliente'})
        r = self.client.post('/api/auth/login', json={'email': ' x@example.com ', 'password': 'clave-ficticia'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(cur.execute.call_args.args[1], ('x@example.com',))
        self.assertNotIn('password_hash', r.json['usuario'])
        with app.app_context():
            self.assertEqual(decode_token(r.json['access_token'])['sub'], '8')
        self.assertCierre(cn, cur)

    def test_login_inexistente_o_clave_incorrecta_401(self):
        for fila in [None, {'id_usuario': 8, 'password_hash': self.hash}]:
            with self.subTest(existe=fila is not None):
                cn, cur = self.base(auth_repository, fila=fila)
                r = self.client.post('/api/auth/login', json={'email': 'x@example.com', 'password': 'incorrecta'})
                self.assertEqual(r.status_code, 401)
                self.assertEqual(r.json, {'error': 'Credenciales inválidas'})
                self.assertCierre(cn, cur)

    def test_compras_usa_identidad_verificada_no_querystring(self):
        self.autenticar()
        cn, cur = self.base(compras, filas=[])
        r = self.client.get('/api/compras?id_usuario=999')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, [])
        self.assertEqual(cur.execute.call_args.args[1], (8,))
        self.assertCierre(cn, cur)

    def test_detalle_propio_vacio_o_con_servicios(self):
        self.autenticar()
        for filas in [[], [{'subtotal': Decimal('6000.00')}]]:
            with self.subTest(filas=len(filas)):
                cn, cur = self.base(compras, fila={'id_compra': 17}, filas=filas)
                r = self.client.get('/api/compras/17/servicios')
                self.assertEqual(r.status_code, 200)
                self.assertEqual(len(r.json), len(filas))
                self.assertEqual(cur.execute.call_args_list[0].args[1], (17, 8))
                self.assertEqual(cur.execute.call_args_list[1].args[1], (17,))
                self.assertCierre(cn, cur)

    def test_detalle_ajeno_o_inexistente_404(self):
        self.autenticar()
        cn, cur = self.base(compras, fila=None)
        self.assertEqual(self.client.get('/api/compras/999/servicios').status_code, 404)
        cur.execute.assert_called_once()
        cur.fetchall.assert_not_called()
        self.assertCierre(cn, cur)

    def test_logout_y_rechazo_posterior(self):
        self.autenticar()
        self.assertEqual(self.client.post('/api/auth/logout').status_code, 200)
        self.assertEqual(self.client.get('/api/compras').status_code, 401)

    def test_fallos_conexion_y_cursor(self):
        self.autenticar()
        with patch.object(compras, 'get_connection', side_effect=Error('fallo simulado')):
            self.assertEqual(self.client.get('/api/compras').status_code, 500)
        cn, cur = self.base(compras)
        cn.cursor.side_effect = Error('fallo simulado')
        self.assertEqual(self.client.get('/api/compras').status_code, 500)
        cn.close.assert_called_once()
        cur.close.assert_not_called()

    def test_json_malformado_y_content_type(self):
        self.autenticar('administrador')
        for ruta in ['/api/auth/login', '/api/servicios']:
            self.assertEqual(self.client.post(ruta, data='{', content_type='application/json').status_code, 400)
            self.assertEqual(self.client.post(ruta, data='texto', content_type='text/plain').status_code, 400)


if __name__ == '__main__':
    unittest.main()
