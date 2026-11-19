# Autenticación

El backend usa Flask-JWT-Extended. Las contraseñas se guardan como hashes con Werkzeug.

## Inicio y cierre de sesión

1. El cliente envía email y contraseña a `POST /api/auth/login`.
2. El backend busca al usuario y comprueba la contraseña con `check_password_hash`.
3. Si son correctos, devuelve el perfil público y un JWT válido durante dos horas.
4. Las solicitudes protegidas envían `Authorization: Bearer <token>`.
5. `POST /api/auth/logout` guarda el identificador del token en `token_revocado` para impedir su reutilización.

El frontend conserva el JWT en su sesión Flask y lo reenvía al backend desde Python.

## Permisos

Las rutas protegidas usan `@jwt_required()` para validar el token. Después llaman a `verificar_acceso` para consultar el usuario y su rol actual en MySQL. El rol enviado por el cliente no concede permisos.

- `401`: token ausente, inválido, vencido o revocado; también usuario inexistente.
- `403`: el usuario está autenticado, pero su rol no permite la operación.
- `500`: no se pudo consultar la base de datos.

## Archivos

- `backend/autenticacion.py`: configura las respuestas de JWT y coordina la revocación.
- `backend/seguridad.py`: obtiene el usuario autenticado y comprueba los roles permitidos.
- `backend/limites.py`: controla los intentos de login y registro por IP y ruta.
- `backend/src/repositories/auth_repository.py`: consultas de usuarios.
- `backend/src/repositories/tokens_repository.py`: consultas de tokens revocados.
- `backend/src/routes/auth_routes.py`: registro, login, perfil y logout.

## Configuración

Definir `SECRET_KEY` en `.env`. Puede usarse una clave distinta en `JWT_SECRET_KEY`; si está vacía, se utiliza `SECRET_KEY`. El archivo `.env` no se publica.

Las bases nuevas incluyen `token_revocado`. Para una base existente, seleccionarla en el cliente MySQL y ejecutar:

```sql
SOURCE backend/db/migraciones/2026_11_02_jwt.sql;
```

La ruta es relativa al directorio desde el que se abrió el cliente MySQL. La migración crea la tabla sin borrar datos existentes. Los vencimientos se guardan en UTC y las filas vencidas se eliminan al cerrar sesiones.

Login y registro permiten hasta 50 intentos por hora y 200 en 24 horas por IP y ruta. Si se supera el límite, responden `429` con `Retry-After`. Los contadores se mantienen en memoria y se reinician con el servidor. Si el frontend intermedia las solicitudes, sus usuarios pueden compartir la IP que recibe el backend.
