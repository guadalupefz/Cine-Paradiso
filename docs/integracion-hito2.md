# Integración del hito 2

## Ejecutar el proyecto

Desde la raíz:

```bash
bash init.sh
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Completar `.env`: datos de MySQL y `SECRET_KEY` con el valor generado. Antes de usar JWT con una base existente, ejecutar la migración indicada en [propuesta-jwt-y-correcciones.md](propuesta-jwt-y-correcciones.md). `FRONTEND_SECRET_KEY` puede tener otra clave; si queda vacía se deriva una clave distinta para el frontend. No publicar `.env`. Si MySQL está en Windows y Python en WSL, usar la dirección del anfitrión y una cuenta habilitada desde WSL; no abrir el puerto a toda la red.

Con el esquema vacío, ejecutar `backend/db/init_db.sql` y después `backend/db/datos_prueba.sql` desde el cliente MySQL. La carga es de una sola ejecución: no es una migración y no debe repetirse sobre datos existentes. El script de creación selecciona `cine_paradiso`; si se usa otra base, adaptar una copia y `DB_NAME`.

```bash
source .venv/bin/activate
python -m backend.crear_admin admin@example.com
python -m backend.app
```

En otra terminal, desde la misma raíz y entorno:

```bash
python frontend/app.py
```

Frontend: http://127.0.0.1:8080. Backend: http://127.0.0.1:5001/api. El registro público siempre crea clientes; el administrador se crea mediante la herramienta de terminal. Los usuarios de la carga ficticia son `ana.demo@example.com` y `luis.demo@example.com`, contraseña `PruebaCine2026!`; no son cuentas para un despliegue público.

## Responsabilidades y contrato

- `backend/db/db.py`: conexión MySQL compartida. Los módulos de compatibilidad reutilizan esa función.
- `backend/src/repositories`: SQL explícito parametrizado.
- `backend/src/services`: reglas y coordinación de operaciones del grupo.
- `backend/src/routes`: validación HTTP, llamadas, respuestas y permisos.
- `backend/seguridad.py`: decoradores `admin_required` y `cualquier_logueado`; verifican JWT y consultan el rol vigente en MySQL.
- `frontend/app.py`: formularios HTML/Jinja y comunicación con backend mediante `requests`, con timeout.

La API utiliza Flask-JWT-Extended. Login conserva la verificación del hash y devuelve access_token. Las rutas reciben Authorization: Bearer <access_token>; logout lo revoca en MySQL. GET /api/usuarios/me devuelve el perfil sin hash. El frontend conserva el token por usuario en su sesión Flask y lo reenvía desde Python. La cookie antigua del backend deja de autenticar: iniciar sesión nuevamente.

Ver [propuesta JWT y correcciones](propuesta-jwt-y-correcciones.md) para preparar la tabla de revocación y revisar el contrato antes de publicar.

401 significa falta de autenticación;403, rol insuficiente;404 también oculta compras ajenas. Los formularios del frontend incluyen un token CSRF. Con HTTPS habilitar `COOKIE_SECURE=1`; no activar debug en una entrega desplegada.

## Funcionalidad integrada

- Login, logout, perfil y consulta de compras propias con detalle de servicios.
- Catálogo, funciones y butacas consultados desde backend.
- Backoffice de películas: búsqueda/importación externa, carga manual y modificación.
- Backoffice de funciones: selección de película/sala, alta y modificación.
- Backoffice de servicios: listado, alta, modificación y eliminación de servicios sin compras. Las FK impiden borrar servicios usados; el precio histórico permanece en `compra_servicio.precio_unitario`.
- Resumen administrativo con las estadísticas y pantalla de QR del equipo.

El precio de servicios se envía como texto decimal (`"2000.00"`), con máximo dos decimales. Los cambios de catálogo no reescriben detalles de compras anteriores.

## Contrato de reservas y películas

- Una reserva queda pendiente durante **15 minutos** desde su creación. El vencimiento se calcula desde la fecha `compra.fecha_hora`; al confirmar, la misma ventana determina si sigue vigente.
- Los estados válidos de compra son `pendiente`, `confirmada`, `expirada`, `cancelada` y `rechazada`. `aprobada` es un valor legado: la migración lo transforma en `confirmada`. Los estados de butaca (`disponible`, `reservada`, `ocupada`) son estados de visualización, no estados de compra.
- `pelicula.duracion_minutos` se almacena como `INT`, en minutos. Para bases existentes, ejecutar `backend/db/migraciones/migration_v2_nov_b09.sql` una sola vez; la migración convierte formatos como `108 min` a `108` y se detiene si encuentra una duración inválida.

La API externa requiere `OMDB_API_KEY`; si no está configurada, el panel informa el problema y permite carga manual. La ruta `/api/pelicula` es la integración externa; `/api/peliculas` es el catálogo local. Son operaciones diferentes y no deben registrarse con el mismo nombre de Blueprint.

## Comprobaciones

```bash
python -m unittest discover -s backend/tests -v
```

La propuesta actual pasa 60 pruebas de regresión y trece escenarios de integración con MySQL 8.4 aislado. Incluye verificación de JWT, revocación persistente, roles, privacidad, reservas concurrentes, vencimiento y formularios administrativos. El detalle y los límites están en propuesta-jwt-y-correcciones.md.

## Pendientes del conjunto

- Reserva temporal/concurrencia y vencimiento: no están demostrados como flujo completo.
- Compra/confirmación: faltan integración de servicios y confirmación de pago según el contrato del equipo.
- Cancelaciones: revisar unicidad función-butaca sin eliminar historial y liberación para reventa.
- Verificar solapamiento de funciones y política de modificación con entradas vendidas.
- Importación externa real con credenciales, proveedor y traducción: debe revisarse con su responsable. La falta de clave se maneja; no se declara verificada una importación real por una prueba local sin proveedor.
- El historial frontend permite consultar compras; cancelación y entradas completas siguen dependiendo de sus endpoints.

No borrar ni reordenar módulos ajenos sin revisar imports y rutas. El arranque incluye todos los Blueprints existentes, en lugar de dejarlos comentados.
