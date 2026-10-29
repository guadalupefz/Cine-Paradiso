# Modelo de datos — Cine Paradiso

## Descripción de las tablas

* **local:** Almacena la información de cada sucursal del cine, incluyendo su nombre y dirección.
* **usuario:** Registra los datos de los usuarios del sistema, incluyendo sus credenciales y rol.
* **pelicula:** Contiene la información de las películas, como título, sinopsis, duración, clasificación y género.
* **sala:** Registra las salas de cada sucursal, incluyendo su nombre y capacidad.
* **funcion:** Almacena las funciones programadas, indicando la película, la sala, el horario y el precio base.
* **compra:** Registra las compras realizadas por los usuarios, junto con la fecha, el importe total y el estado de la operación.
* **entrada:** Representa cada entrada comprada e incluye la función, el código de butaca, el token QR individual y la fecha de validación.
* **servicio_adicional:** Almacena los productos o servicios adicionales disponibles y sus precios vigentes.
* **compra_servicio:** Relaciona los servicios adicionales con una compra e indica la cantidad y el precio unitario al momento de la compra.

## Relaciones principales

Las sucursales contienen salas, que se utilizan para programar funciones. Cada función corresponde a una película y una sala. Los usuarios pueden realizar compras que incluyen una o varias entradas y servicios adicionales. Cada entrada corresponde a una función y tiene un código QR único. Los servicios adicionales se relacionan con las compras mediante la tabla `compra_servicio`.

## Restricciones importantes

Se utilizan claves primarias (PK) para identificar los registros y claves foráneas (FK) para relacionar las tablas. También se establecen restricciones `UNIQUE` para evitar duplicados, como el correo electrónico del usuario, el nombre de los servicios adicionales y el código QR de cada entrada. Asimismo, se evita vender la misma butaca más de una vez para una misma función.

El precio unitario de los servicios adicionales se conserva en cada compra para mantener el importe original, aunque los precios vigentes cambien posteriormente.
