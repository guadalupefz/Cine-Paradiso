# Modelo de datos — Cine Paradiso

## Descripción de las tablas

- **local:** Almacena la información de cada sucursal del cine, incluyendo su nombre y dirección.
- **usuario:** Registra los datos de los usuarios del sistema, incluyendo sus credenciales y rol.
- **pelicula:** Contiene la información de las películas, como título, sinopsis, póster, duración, clasificación y género. El campo `poster` se utilizará para almacenar la URL de la imagen del póster obtenida desde una API externa.
- **sala:** Registra las salas de cada sucursal, incluyendo su nombre y capacidad.
- **butaca:** Identifica las butacas de cada sala mediante su fila y número, evitando que existan dos butacas con la misma ubicación dentro de una sala.
- **funcion:** Almacena las funciones programadas, indicando la película, la sala, la fecha y hora de inicio y el precio base.
- **compra:** Registra las compras realizadas por los usuarios, junto con la fecha, el importe total y el estado de la operación.
- **entrada:** Representa cada entrada comprada e incluye la compra a la que pertenece, la función, la butaca asignada, el token QR individual y la fecha de validación.
- **servicio_adicional:** Almacena los productos o servicios adicionales disponibles y sus precios vigentes.
- **compra_servicio:** Relaciona los servicios adicionales con una compra e indica la cantidad adquirida y el precio unitario al momento de la compra.

## Relaciones principales

Las sucursales contienen salas, que a su vez tienen butacas. Las salas se utilizan para programar funciones, y cada función corresponde a una película y una sala.

Los usuarios pueden realizar compras que incluyen una o varias entradas y servicios adicionales. Cada entrada corresponde a una función y una butaca, y cuenta con un código QR único para validar el ingreso.

Los servicios adicionales se relacionan con las compras mediante la tabla `compra_servicio`. Esta tabla permite registrar la cantidad adquirida y conservar el precio unitario que tenía el servicio al momento de la compra.

La información de los pósteres se obtiene de una API externa y se almacena como una URL en el campo `poster` de la tabla `pelicula`.

## Restricciones importantes

- Se utilizan claves primarias (PK) para identificar los registros y claves foráneas (FK) para relacionar las tablas.
- El correo electrónico de cada usuario debe ser único.
- El nombre de cada sala debe ser único dentro de una misma sucursal.
- Cada butaca debe tener una ubicación única dentro de su sala, definida por su fila y número.
- El nombre de cada servicio adicional debe ser único.
- El token QR de cada entrada debe ser único.
- Se evita vender la misma butaca más de una vez para una misma función mediante una restricción `UNIQUE` sobre `id_funcion` e `id_butaca`.
- El precio unitario de los servicios adicionales se conserva en cada compra para mantener el importe original, aunque los precios vigentes cambien posteriormente.

## Consideraciones

El campo `poster` almacena la URL de la imagen, no el archivo de imagen en sí. La API externa proporciona esa información y la aplicación la utiliza para mostrar el póster de cada película.

Actualmente, la restricción `UNIQUE` de la tabla `entrada` impide registrar otra entrada para la misma butaca y función, incluso si la entrada anterior fue cancelada. Si el sistema necesita permitir la reventa de una butaca después de una cancelación, será necesario revisar esa restricción.
