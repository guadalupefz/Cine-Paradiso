-- Datos ficticios para desarrollo. Cargar UNA VEZ tras crear las tablas.
-- Seleccionar antes la base de destino con USE.
-- Usar una base de desarrollo con las tablas vacias, no la carga manual anterior.
-- No borra datos ni crea tablas. Las capacidades pequenas son para pruebas.
-- Clave de ambas cuentas ficticias: PruebaCine2026!
-- No son cuentas de produccion ni usuarios de acceso al servidor MySQL.

SET NAMES utf8mb4;
START TRANSACTION;

INSERT INTO local (nombre, direccion)
VALUES ('Cine Paradiso - Demo', 'Calle Ficticia 123');
SET @local_prueba = LAST_INSERT_ID();

INSERT INTO sala (id_local, nombre, capacidad)
VALUES (@local_prueba, 'Sala Azul Demo', 2);
SET @sala_azul = LAST_INSERT_ID();

INSERT INTO sala (id_local, nombre, capacidad)
VALUES (@local_prueba, 'Sala Roja Demo', 1);
SET @sala_roja = LAST_INSERT_ID();

INSERT INTO butaca (id_sala, fila, numero)
VALUES (@sala_azul, 'A', 1);
SET @butaca_azul_a1 = LAST_INSERT_ID();

INSERT INTO butaca (id_sala, fila, numero)
VALUES (@sala_azul, 'A', 2);
SET @butaca_azul_a2 = LAST_INSERT_ID();

INSERT INTO butaca (id_sala, fila, numero)
VALUES (@sala_roja, 'A', 1);
SET @butaca_roja_a1 = LAST_INSERT_ID();

SET @hash_prueba = 'scrypt:32768:8:1$fIBRjxgeb8vKcOPM$ad67a65fe12f0488c33848cdcb96ff6096ec37c08f817f5dddff97b657fd0bda65e57e5da352be33ee5f501bb69251d5ee08f9b637aeae8611362ad0986547dd';

INSERT INTO usuario (nombre, apellido, email, password_hash, rol)
VALUES ('Ana', 'Prueba', 'ana.demo@example.com', @hash_prueba, 'cliente');
SET @usuario_ana = LAST_INSERT_ID();

INSERT INTO usuario (nombre, apellido, email, password_hash, rol)
VALUES ('Luis', 'Prueba', 'luis.demo@example.com', @hash_prueba, 'cliente');
-- Luis queda sin compras para comprobar aislamiento y listas vacias.

INSERT INTO pelicula (titulo, sinopsis, poster, duracion_minutos, clasificacion, genero)
VALUES ('Aventura de prueba', 'Pelicula ficticia para desarrollo.', '/static/img/default.svg', '108 min', '+13', 'Aventura');
SET @pelicula_prueba = LAST_INSERT_ID();
-- Poster de demostracion servido por el backend.

INSERT INTO funcion (id_pelicula, id_sala, fecha_hora_inicio, precio_base)
VALUES (@pelicula_prueba, @sala_azul, DATE_ADD(NOW(), INTERVAL 7 DAY), 8000.00);
SET @funcion_primera = LAST_INSERT_ID();

INSERT INTO funcion (id_pelicula, id_sala, fecha_hora_inicio, precio_base)
VALUES (@pelicula_prueba, @sala_azul, DATE_ADD(DATE_ADD(NOW(), INTERVAL 7 DAY), INTERVAL 3 HOUR), 8000.00);
SET @funcion_segunda = LAST_INSERT_ID();

INSERT INTO servicio_adicional (nombre, precio)
VALUES ('Pochoclos Demo', 5000.00);
SET @servicio_pochoclos = LAST_INSERT_ID();

INSERT INTO servicio_adicional (nombre, precio)
VALUES ('Agua Demo', 2000.00);
SET @servicio_agua = LAST_INSERT_ID();

INSERT INTO servicio_adicional (nombre, precio)
VALUES ('Caramelos Demo', 1000.00);
-- Caramelos queda sin compras para comprobar LEFT JOIN/COUNT.

-- Una entrada de8000 + dos pochoclos a4500 historicos + un agua a2000 =19000.
INSERT INTO compra (id_usuario, total, estado)
VALUES (@usuario_ana, 19000.00, 'aprobada');
SET @compra_con_servicios = LAST_INSERT_ID();

INSERT INTO entrada (id_compra, id_funcion, id_butaca, qr_token)
VALUES (@compra_con_servicios, @funcion_primera, @butaca_azul_a1, 'demo-entrada-primera-no-produccion');

INSERT INTO compra_servicio (id_compra, id_servicio, cantidad, precio_unitario)
VALUES
    (@compra_con_servicios, @servicio_pochoclos, 2, 4500.00),
    (@compra_con_servicios, @servicio_agua, 1, 2000.00);
-- Precio historico4500 distinto del catalogo5000, de forma intencional.

INSERT INTO compra (id_usuario, total, estado)
VALUES (@usuario_ana, 8000.00, 'aprobada');
SET @compra_sin_servicios = LAST_INSERT_ID();

-- Mismo asiento fisico que antes, pero en otra funcion: es valido.
INSERT INTO entrada (id_compra, id_funcion, id_butaca, qr_token)
VALUES (@compra_sin_servicios, @funcion_segunda, @butaca_azul_a1, 'demo-entrada-segunda-no-produccion');

COMMIT;
