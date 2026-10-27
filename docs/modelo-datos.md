# Modelo de datos — Cine Paradiso

## Descripción de las tablas

* **local:** Almacena la información de cada sucursal del cine, como su nombre, dirección y estado activo.
* **usuario:** Registra los datos de los usuarios del sistema, incluyendo sus credenciales y rol (cliente o administrador).
* **pelicula:** Contiene la información de las películas y permite su activación o desactivación sin perder información histórica.
* **genero:** Almacena los géneros cinematográficos disponibles.
* **pelicula_genero:** Relaciona las películas con sus géneros, permitiendo que una película tenga varios géneros y que un género corresponda a varias películas.
* **sala:** Registra las salas de cada sucursal y su información básica.
* **butaca:** Representa los asientos de cada sala, identificados por fila y número.
* **funcion:** Almacena las funciones programadas, indicando la película, la sala, el horario y el precio base.
* **compra:** Registra las compras realizadas por los usuarios, junto con la fecha, el importe total y el estado de la operación. En caso de cancelación, almacena la fecha y el motivo de cancelación para conservar el historial de la compra.
* **entrada:** Representa cada entrada comprada e incluye la función, la butaca, el precio, el estado y un código QR individual.
* **servicio_extra:** Almacena los productos o servicios adicionales disponibles, permitiendo activarlos o desactivarlos sin eliminar registros históricos.
* **detalle_servicio_compra:** Relaciona los servicios adicionales con una compra e indica la cantidad y el precio unitario al momento de la compra.

## Relaciones principales
Las sucursales contienen salas, y cada sala tiene butacas. Las funciones vinculan una película con una sala y un horario determinado. Los usuarios pueden realizar compras, que pueden incluir una o varias entradas y servicios adicionales. Cada entrada corresponde a una función y una butaca, y cuenta con su propio código QR. Las películas se relacionan con sus géneros mediante la tabla `pelicula_genero`.

## Restricciones importantes
Se utilizan claves primarias (PK) para identificar los registros y claves foráneas (FK) para relacionar las tablas. También se establecen restricciones `UNIQUE` en los campos que no deben repetirse, como el correo electrónico del usuario, el nombre del género y el código QR de cada entrada. En las butacas, se evita repetir la misma combinación de sala, fila y número. Asimismo, una butaca no puede venderse más de una vez para una misma función. Las compras canceladas conservan su información histórica mediante cambios de estado, sin eliminar registros del sistema.

Algunas entidades utilizarán un campo activo para implementar bajas lógicas y conservar el historial de información. Esta estrategia se aplicará principalmente a usuarios, películas, salas y servicios adicionales, evitando eliminar registros que puedan estar asociados a compras, entradas o estadísticas históricas.
