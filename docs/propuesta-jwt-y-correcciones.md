# Autenticación JWT y correcciones de integración

## Alcance de esta propuesta

Actualización sobre develop: autenticación JWT y correcciones verificadas. Se incorpora Flask-JWT-Extended y se corrigen defectos de B08, B10, B11 y B12 que figuraban como completas. No se considera cerrada C11 por escribir este documento ni se completan cancelación, lector de cámara o correo de reservas en nombre de sus responsables.

## Contraseñas y autenticación son cosas diferentes

El registro sigue guardando `password_hash`, generado con `werkzeug.security.generate_password_hash`. El login verifica con `check_password_hash`. No se guardan contraseñas dentro de un JWT.

Después de verificar credenciales, `create_access_token(identity=str(id_usuario))` emite el JWT. Las rutas protegidas usan Flask-JWT-Extended para comprobar firma y vencimiento. Los decoradores de `backend/seguridad.py` consultan además el usuario y su rol vigente en MySQL: un campo de rol enviado por el cliente no concede permisos.

Se usa el mismo mecanismo para clientes y administradores. Así el login, los endpoints de compras y el backoffice no dependen de credenciales incompatibles. Los nombres de rutas y las firmas que reciben el ID verificado se mantienen.

## Cambios que deben conocer quienes prueban endpoints

- `POST /api/auth/login` agrega `access_token`, `token_type: "Bearer"` y `expires_in: 7200`, conservando el mensaje y el perfil público.
- Enviar `Authorization: Bearer <access_token>` en las rutas autenticadas.
- `POST /api/auth/logout` necesita ese token y lo revoca en MySQL. Se rechaza su reutilización incluso desde otra instancia de la aplicación.
- Falta de token, token inválido/vencido/revocado: 401. Rol insuficiente: 403.
- Las cookies anteriores de autenticación del backend dejan de servir. Los usuarios deben iniciar sesión nuevamente.
- El frontend sigue usando sesión Flask para sus formularios; guarda el token individualmente y lo transmite desde Python mediante requests. El navegador no hace fetch ni AJAX. Los formularios mantienen CSRF.
- No se agregan refresh tokens: a las dos horas se inicia sesión otra vez.

## Preparación de una base existente

1. Instalar las dependencias actualizadas: `python -m pip install -r requirements.txt`.
2. Seleccionar la base correcta en MySQL.
3. Ejecutar `backend/db/migraciones/2026_11_02_jwt.sql` con una cuenta que tenga CREATE.
4. Conservar los valores privados de `.env`. `JWT_SECRET_KEY` puede tener una clave propia; si está vacía se utiliza SECRET_KEY. No usar las claves ficticias de las pruebas.
5. Reiniciar backend y frontend e iniciar sesión nuevamente.

La migración es idempotente: crea solamente `token_revocado(jti, vence_en)`. No borra usuarios, compras ni entradas. La creación inicial de una base nueva ya incluye esa tabla. No volver a ejecutar init_db.sql ni datos_prueba.sql sobre la base manual existente.

La tabla conserva el identificador del token revocado, no el JWT completo ni una contraseña. Los vencimientos se guardan en UTC y las filas vencidas se limpian al cerrar sesiones.

## Correcciones incluidas

- **B08:** leer tanto `108` como el formato antiguo `108 min`; las nuevas importaciones/carga guardan minutos numéricos. Se conserva VARCHAR en el esquema actual para no imponer una migración de la columna sin coordinarla.
- **B08/I06:** no cambiar duración de una película con funciones programadas. El resto de los campos puede editarse. Reprogramar antes de modificar una duración evita introducir solapamientos desde el catálogo.
- **B08:** no sustituir película, sala u horario de una función con entradas vendidas.
- **B10/B11:** distinguir disponible, reservada vigente y ocupada; ignorar reservas vencidas al mostrar disponibilidad.
- **B11:** comprobar que cada butaca pertenezca a la sala de la función antes de crear compra/entradas.
- **B11:** bloquear primero la fila de la función para ordenar reservas concurrentes. Tratar 1205/1213 como conflictos recuperables; mantener las restricciones UNIQUE.
- **B11:** reconocer compras aprobada/confirmada como ocupadas y liberar las entradas de toda la reserva vencida de esa función, conservando la compra expirada.
- **B11:** validar tipos de IDs antes de buscar duplicados con set; JSON inválido devuelve 400.
- **B12:** compra directa comparte bloqueo y limpieza, para no competir fuera del control de reservas. Se corrige el cierre si falla crear el cursor.

## Validación realizada

- 60 pruebas unitarias/regresión con Flask real y MySQL simulado.
- 13 escenarios con MySQL 8.4 real aislado: JWT/roles/vencimiento, logout persistente, privacidad, reservas y JSON inválido, vencimiento completo, confirmación y estados, duración heredada, protección de programación, servicios y frontend.
- Ocho pares de reservas simultáneas: en todos, una creación 201 y un conflicto 409, con una sola entrada persistida.
- Compra directa contra reserva simultánea: sin duplicación ni error interno en el caso ejecutado.
- Frontend→requests→backend→MySQL: login JWT, panel y formularios de servicios, protección CSRF y logout real.

Estos resultados no verifican una importación real con OMDb, entrega SMTP o escaneo con cámara. Los módulos en proceso del equipo conservan su estado.

## Ayudantes SQL del importador

Se incorporó ejecutar_buscar_uno del archivo de Alberto al paquete backend/db. Usar `from backend.db import ejecutar_buscar, ejecutar_buscar_uno, ejecutar_guardar`.

- `backend/db/db.py` define get_connection con la configuración común.
- `backend/db/__init__.py` exporta los ayudantes; todos usan ese conector.
- ejecutar_buscar devuelve una lista; ejecutar_buscar_uno devuelve un diccionario o None.
- Se conservan exito/datos/mensaje y el ID de las escrituras. Las escrituras confirman o revierten antes de cerrar.
- No restaurar un segundo backend/db.py ni reemplazar backend/db/db.py por un archivo sin get_connection.

Se probaron éxito, ausencia, parámetros, fallos, commit/rollback y cierres, además de una ejecución con MySQL real.

## Pendientes que siguen fuera de este cambio

- **C11:** aprobación del contrato JWT y decisiones de plazo de reserva (documento 10 minutos/código 15), proveedor e identificador externo.
- **B13/I05:** integrar la cancelación que el equipo esté desarrollando y su liberación sin perder historial.
- **B14/I07:** probar el lector y la validación desde cámara; no se reemplaza el módulo que acaba de publicar el equipo.
- **B15:** conectar correo a confirmación de reservas y probar SMTP/reintento sin duplicar compras.
- **I03/I04:** completar el recorrido cliente de selección/reserva/servicios/pago, enviando IDs reales de butaca.

Referencia de la biblioteca: https://flask-jwt-extended.readthedocs.io/en/stable/basic_usage.html
