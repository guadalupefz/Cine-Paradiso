import os
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit,parse_qs

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class RegistroFrontend(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client=frontend.app.test_client()
        self.resultado=({'message':'Usuario registrado','usuario':{'id_usuario':8,'rol':'cliente'}},201)
        self.llamadas=[]
        self.datos={'nombre':'Julieta','apellido':'Prueba','email':'julieta@example.com','password':'ClaveFicticia123!','confirmar_password':'ClaveFicticia123!'}
        with self.client.session_transaction() as sesion:sesion['csrf_token']='csrf-prueba'
        parche=patch.object(frontend,'llamar_backend',side_effect=self.backend)
        parche.start()
        self.addCleanup(parche.stop)

    def backend(self,metodo,ruta,**datos):
        self.llamadas.append((metodo,ruta,datos))
        if ruta=='/auth/registro':return self.resultado
        return [],200

    def post(self,**datos):
        return self.client.post('/registro',data={'csrf_token':'csrf-prueba',**self.datos,**datos})

    def test_registro_envia_solo_campos_del_contrato(self):
        respuesta=self.post(rol='administrador')
        self.assertEqual(respuesta.status_code,302)
        enviada=next(datos['json'] for _,ruta,datos in self.llamadas if ruta=='/auth/registro')
        self.assertEqual(enviada,{clave:self.datos[clave] for clave in ('nombre','apellido','email','password')})
        with self.client.session_transaction() as sesion:
            self.assertNotIn('backend_token',sesion)
            self.assertNotIn('password',sesion)

    def test_cuenta_creada_continua_en_login_con_destino_y_email(self):
        destino='/compra?id_funcion=15&butacas=A1%2CA2'
        respuesta=self.post(next=destino)
        self.assertEqual(urlsplit(respuesta.location).path,'/login')
        siguiente=parse_qs(urlsplit(respuesta.location).query)['next'][0]
        self.assertEqual(parse_qs(urlsplit(siguiente).query)['butacas'],['A1,A2'])
        login=self.client.get(respuesta.location)
        self.assertIn('value="julieta@example.com"',login.text)
        self.assertIn('Tu cuenta fue creada',login.text)

    def test_confirmacion_distinta_no_crea_cuenta(self):
        respuesta=self.post(confirmar_password='otra')
        self.assertEqual(respuesta.status_code,400)
        self.assertIn('Las contraseñas no coinciden',respuesta.text)
        self.assertFalse(any(ruta=='/auth/registro' for _,ruta,_ in self.llamadas))

    def test_email_duplicado_conserva_datos_pero_no_contrasena(self):
        self.resultado=({'errors':[{'message':'El correo ya está registrado.'}]},409)
        respuesta=self.post(next='/butacas/15?id_pelicula=3')
        self.assertEqual(respuesta.status_code,409)
        self.assertIn('El correo ya está registrado.',respuesta.text)
        self.assertIn('value="Julieta"',respuesta.text)
        self.assertIn('value="julieta@example.com"',respuesta.text)
        self.assertNotIn('value="ClaveFicticia123!"',respuesta.text)

    def test_validacion_backend_se_muestra(self):
        self.resultado=({'errors':[{'message':'El email no tiene un formato válido.'}]},400)
        respuesta=self.post(email='invalido')
        self.assertEqual(respuesta.status_code,400)
        self.assertIn('El email no tiene un formato válido.',respuesta.text)

    def test_fallo_servidor_conserva_email_y_destino(self):
        self.resultado=({'error':'No se pudo conectar con el servidor'},503)
        respuesta=self.post(next='/butacas/15')
        self.assertEqual(respuesta.status_code,503)
        self.assertIn('value="julieta@example.com"',respuesta.text)
        self.assertIn('value="/butacas/15"',respuesta.text)

    def test_next_externo_no_se_propaga_a_login(self):
        respuesta=self.post(next='https://evil.example')
        self.assertEqual(respuesta.location,'/login')

    def test_sin_csrf_no_crea_cuenta(self):
        respuesta=self.client.post('/registro',data=self.datos)
        self.assertEqual(respuesta.status_code,400)
        self.assertFalse(any(ruta=='/auth/registro' for _,ruta,_ in self.llamadas))


if __name__=='__main__':unittest.main()
