# Listado de endpoints de Cine Paradiso

## Usuarios y autenticación

- `POST /api/auth/registro` — Registrar un usuario.
- `POST /api/auth/login` — Iniciar sesión.
- `GET /api/usuarios/me` — Obtener los datos del usuario autenticado.
- `PUT /api/usuarios/me` — Modificar los datos del usuario.
- `GET /api/usuarios` — Listar usuarios (administrador).

## Películas, locales y funciones

- `GET /api/locales` — Listar locales.
- `GET /api/locales/{id}/salas` — Listar las salas de un local.
- `GET /api/peliculas` — Listar películas.
- `GET /api/cartelera` — Consultar la cartelera.
- `GET /api/funciones` — Listar funciones disponibles.
- `POST /api/funciones` — Crear una función (administrador).
- `PUT /api/funciones/{id}` — Modificar una función (administrador).
- `POST /api/peliculas/sincronizar` — Sincronizar películas con una API externa (administrador).

## Butacas y compras

- `GET /api/funciones/{id}/butacas` — Consultar las butacas disponibles para una función.
- `POST /api/funciones/{id}/reservas` — Reservar butacas para una función.
- `POST /api/compras` — Crear una compra de entradas.
- `GET /api/compras` — Consultar las compras del usuario.
- `GET /api/compras/{id}` — Consultar los detalles de una compra.
- `POST /api/compras/{id}/confirmar` — Confirmar una compra.
- `POST /api/compras/{id}/cancelar` — Cancelar una compra, si cumple las condiciones establecidas.

## Entradas y validación por QR

- `GET /api/compras/{id}/entradas` — Consultar las entradas de una compra.
- `GET /api/entradas/{id}/qr` — Obtener el código QR de una entrada.
- `POST /api/qr/validar` — Validar un código QR.
- `POST /api/qr/registrar-ingreso` — Registrar el ingreso con una entrada validada.

## Servicios adicionales

- `GET /api/servicios` — Listar los servicios adicionales disponibles.

## Estadísticas

- `GET /api/estadisticas/ventas` — Consultar estadísticas de ventas (administrador).
- `GET /api/estadisticas/ocupacion` — Consultar estadísticas de ocup
