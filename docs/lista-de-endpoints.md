# Listado de endpoints de Cine Paradiso

## Usuarios y autenticación

- `POST /api/auth/registro` — Registrar un usuario.
  Permiso: Público.

- `POST /api/auth/login` — Iniciar sesión.
  Permiso: Público.

- `GET /api/usuarios/me` — Obtener los datos del usuario autenticado.
  Permiso: Usuario autenticado.

- `PUT /api/usuarios/me` — Modificar los datos del usuario.
  Permiso: Usuario autenticado.

- `GET /api/usuarios` — Listar usuarios (administrador).
  Permiso: Administrador.

## Películas, locales y funciones

- `GET /api/locales` — Listar locales.
  Permiso: Público.

- `GET /api/locales/{id}/salas` — Listar las salas de un local.
  Permiso: Público.

- `GET /api/peliculas` — Listar películas.
  Permiso: Público.

- `GET /api/cartelera` — Consultar la cartelera.
  Permiso: Público.

- `GET /api/funciones` — Listar funciones disponibles.
  Permiso: Público.

- `POST /api/funciones` — Crear una función.
  Permiso: Administrador.

- `PUT /api/funciones/{id}` — Modificar una función.
  Permiso: Administrador.

- `POST /api/peliculas/sincronizar` — Sincronizar películas con una API externa.
  Permiso: Administrador.

## Butacas y compras

- `GET /api/funciones/{id}/butacas` — Consultar las butacas disponibles para una función.
  Permiso: Usuario autenticado.

- `POST /api/funciones/{id}/reservas` — Reservar butacas para una función.
  Permiso: Usuario autenticado.

- `POST /api/compras` — Crear una compra de entradas.
  Permiso: Usuario autenticado.

- `GET /api/compras` — Consultar las compras del usuario.
  Permiso: Usuario autenticado.

- `GET /api/compras/{id}` — Consultar los detalles de una compra.
  Permiso: Usuario autenticado.

- `POST /api/compras/{id}/confirmar` — Confirmar una compra.
  Permiso: Usuario autenticado.

- `POST /api/compras/{id}/cancelar` — Cancelar una compra.
  Permiso: Usuario autenticado (propietario de la compra).

## Entradas y validación por QR

- `GET /api/compras/{id}/entradas` — Consultar las entradas de una compra.
  Permiso: Usuario autenticado.

- `GET /api/entradas/{id}/qr` — Obtener el código QR de una entrada.
  Permiso: Usuario autenticado.

- `POST /api/qr/validar` — Validar un código QR.
  Permiso: Administrador.

- `POST /api/qr/registrar-ingreso` — Registrar el ingreso con una entrada validada.
  Permiso: Administrador.
## Servicios adicionales

- `GET /api/servicios` — Listar los servicios adicionales disponibles.
  Permiso: Público.

## Estadísticas

- `GET /api/estadisticas/ventas` — Consultar estadísticas de ventas.
  Permiso: Administrador.

- `GET /api/estadisticas/ocupacion` — Consultar estadísticas de ocupación.
  Permiso: Administrador.

  ## Estados HTTP utilizados

  Estados HTTP utilizados

- 200 OK: Operación realizada correctamente.
- 201 Created: Recurso creado correctamente.
- 400 Bad Request: Datos inválidos o incompletos.
- 401 Unauthorized: Usuario no autenticado.
- 403 Forbidden: Usuario sin permisos suficientes.
- 404 Not Found: Recurso inexistente.
- 500 Internal Server Error: Error interno del servidor.
