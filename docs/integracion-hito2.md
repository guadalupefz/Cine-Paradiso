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

## Ejecución con Docker Compose

La alternativa contenerizada levanta MySQL, backend y frontend:

```bash
cp .env.example .env
docker compose up --build
```

El contenedor de MySQL crea `DB_USER` con `DB_PASSWORD` y la base `DB_NAME`.
También monta `backend/db/init_db.sql` en el directorio de inicialización de
MySQL, por lo que el esquema se carga solamente al crear el volumen por primera
vez. Los healthchecks esperan que MySQL, backend y frontend estén listos antes
de habilitar sus dependencias.

Para cargar datos de prueba una vez que MySQL esté disponible:

```bash
docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < backend/db/datos_prueba.sql
```

Después del arranque:

- Frontend: http://127.0.0.1:8080
- Backend: http://127.0.0.1:5001/api

Si se modifica la configuración de la base o se necesita iniciar desde cero,
eliminar también su volumen persistente:

```bash
docker compose down -v
docker compose up --build
```

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

Login y registro limitan los intentos por IP y endpoint: hasta 50 por hora y 200 en las últimas 24 horas. El exceso devuelve 429 con la cabecera Retry-After en segundos. También cuentan los intentos inválidos. Los contadores de ambas operaciones son independientes y las consultas de cartelera o compras no consumen ese cupo. Se guardan en memoria por instancia de aplicación y se reinician con el proceso; no son un límite compartido entre varios procesos. Se utiliza la IP que recibe directamente el backend: si el frontend funciona como intermediario, sus usuarios pueden compartir ese cupo. No se confía en cabeceras de IP suministradas por el cliente.

## Funcionalidad integrada

- Login, logout, perfil y consulta de compras propias con detalle de servicios.
- Catálogo, funciones y butacas consultados desde backend.
- Backoffice de películas: búsqueda/importación externa, carga manual y modificación.
- Backoffice de funciones: selección de película/sala, alta y modificación.
- Backoffice de servicios: listado, alta, modificación y eliminación de servicios sin compras. Las FK impiden borrar servicios usados; el precio histórico permanece en `compra_servicio.precio_unitario`.
- Resumen administrativo con las estadísticas y pantalla de QR del equipo.
- Reseñas de películas: un cliente puede publicar o editar una reseña por película
  únicamente después de que una de sus entradas haya sido validada por QR.
  La puntuación va de 1 a 5 y el comentario es opcional (máximo 1000 caracteres).
- El resumen administrativo permite descargar un PDF con ventas por género y
  franja horaria, cancelaciones y ocupación por función y película.

Para una base existente, ejecutar `backend/db/migraciones/2026_11_14_resenas.sql`
una vez con la base `cine_paradiso` seleccionada. El esquema inicial ya incluye
la tabla `resena`.

El precio de servicios se envía como texto decimal (`"2000.00"`), con máximo dos decimales. Los cambios de catálogo no reescriben detalles de compras anteriores.

Los servicios requieren `nombre`, `descripcion` y `precio`. El backoffice conserva los tres campos al crear, editar o corregir un error. Para una base antigua que no tenga `servicio_adicional.descripcion`, seleccionar la base correspondiente y ejecutar `backend/db/migraciones/2026_11_11_descripcion_servicios.sql`. La migración conserva los datos y utiliza el nombre como descripción inicial cuando falta. No ejecutar otra vez `init_db.sql` sobre una base ya utilizada.

Instalar las dependencias desde `requirements.txt` en la raíz antes de iniciar ambas aplicaciones. Los archivos por componente también declaran Flask-Mail en backend y ReportLab en frontend.

### Imágenes de servicios

Frontend y backend admiten solicitudes de hasta 5 MiB, incluido el formulario y su imagen. Una carga que supere ese límite devuelve HTTP 413: JSON en la API y un mensaje en español en la web. El límite se aplica en ambas aplicaciones para que una imagen válida no quede bloqueada antes de llegar al backend.

El backoffice envía los campos con formulario y, si se seleccionó una imagen, con `multipart/form-data`. La API conserva también el contrato JSON para nombre, descripción y precio. La imagen es opcional: al crear sin imagen se guarda una cadena vacía; al editar sin subir otra se conserva la anterior. Se admiten extensiones PNG, JPG, JPEG y WEBP; se genera un nombre único y se guardan bajo `backend/static/img/servicios`. Si falla la escritura SQL, se descarta el archivo nuevo de esa operación.

Para bases existentes seleccionar primero la base y ejecutar `backend/db/migraciones/migracion_imagen_servicios.sql`. Puede repetirse, añade la columna si falta y normaliza los NULL antiguos sin cambiar rutas existentes. La migración de descripción es independiente y también debe ejecutarse en bases antiguas. No importar el esquema inicial encima de una base utilizada.

## Eliminación de salas y locales

El backoffice muestra acciones de eliminación con confirmación. `DELETE /api/salas/<id_sala>` elimina una sala y sus butacas; `DELETE /api/locales/<id_local>` elimina el local, sus salas y sus butacas. Ambas rutas exigen JWT de administrador y rechazan con 409 cualquier función o entrada asociada, incluso si la función todavía no tiene ventas. Los registros inexistentes devuelven 404. Se usan bloqueos y una transacción; una dependencia o error revierte toda la operación. El frontend envía las operaciones desde formularios POST protegidos con CSRF, mediante Python requests.

## Contrato de reservas y películas

- Una reserva queda pendiente durante **15 minutos** desde su creación. El vencimiento se calcula desde la fecha `compra.fecha_hora`; al confirmar, la misma ventana determina si sigue vigente.
- Los estados válidos de compra son `pendiente`, `confirmada`, `expirada`, `cancelada` y `rechazada`. `aprobada` es un valor legado: la migración lo transforma en `confirmada`. Los estados de butaca (`disponible`, `reservada`, `ocupada`) son estados de visualización, no estados de compra.
- `pelicula.duracion_minutos` se almacena como `INT`, en minutos. Para bases existentes, ejecutar `backend/db/migraciones/migration_v2_nov_b09.sql` una sola vez; la migración convierte formatos como `108 min` a `108` y se detiene si encuentra una duración inválida.

La API externa requiere `OMDB_API_KEY`; si no está configurada, el panel informa el problema y permite carga manual. La ruta `/api/pelicula` es la integración externa; `/api/peliculas` es el catálogo local. Son operaciones diferentes y no deben registrarse con el mismo nombre de Blueprint.

## Comprobaciones

```bash
python -m unittest discover -s backend/tests -v
```

Ejecutar también `python -m unittest discover -s frontend/tests -v`. Las pruebas de contrato de servicios usan el validador real del backend para no aceptar campos incompletos en la simulación. Los tests con sustitutos verifican lógica, errores y formularios; no sustituyen una prueba de compra completa con MySQL, SMTP y el proveedor externo en el entorno donde se presente el proyecto. Las verificaciones históricas con una base aislada se describen en propuesta-jwt-y-correcciones.md y no acreditan el entorno actual.

## Pendientes del conjunto

- Reserva temporal, confirmación, servicios y cancelación ya tienen implementación; verificar el flujo completo y migraciones con una base real antes de marcar la integración como terminada.
- Comprobar unicidad de ocupación activa y liberación para reventa con solicitudes concurrentes; los tests simulados no comprueban índices MySQL.
- Verificar solapamiento de funciones y política de modificación con entradas vendidas.
- Importación externa real con credenciales, proveedor y traducción: debe revisarse con su responsable. La falta de clave se maneja; no se declara verificada una importación real por una prueba local sin proveedor.
- El historial frontend permite consultar compras; cancelación y entradas completas siguen dependiendo de sus endpoints.

No borrar ni reordenar módulos ajenos sin revisar imports y rutas. El arranque incluye todos los Blueprints existentes, en lugar de dejarlos comentados.


## Configurar OMDb e importar películas

Cada instalación debe tener su propia configuración privada en `.env`:

```dotenv
OMDB_API_KEY=clave_recibida_de_omdb
```

No publicar la clave ni el archivo `.env`. Reiniciar el backend al modificar esa configuración.

Si la base ya existe, seleccionar la base del proyecto y ejecutar una sola vez la ampliación del campo del póster:

```sql
SOURCE backend/db/migraciones/2026_11_18_ampliar_poster.sql;
```

La ruta del archivo es relativa al directorio desde el que se inició el cliente MySQL. La migración amplía `pelicula.poster` a 2048 caracteres y conserva sus datos. No volver a ejecutar `init_db.sql` sobre la base existente. Las bases nuevas ya incluyen el campo ampliado.

Desde Administración → Películas se consulta un título y se elige Importar al catálogo. El formulario utiliza GET/POST `/api/pelicula`; búsqueda, detalle e importación por IMDb ID también están disponibles en `/api/peliculas/omdb/...`. Todas estas operaciones requieren administrador.

La importación devuelve 201 al crear y 200 al actualizar el mismo IMDb ID. Si la película ya tiene funciones programadas, no permite cambiar su duración al reimportar. Una respuesta incompleta o demasiado larga para el esquema se rechaza antes de guardar; sin póster se usa la imagen predeterminada existente. La duración de la ficha externa se muestra como la devuelve OMDb y se guarda como minutos enteros.

La clave se utiliza en el backend. El navegador no la necesita ni debe recibirla.
