-- Inicialización de la base de datos
CREATE DATABASE IF NOT EXISTS cine_paradiso;
USE cine_paradiso;

-- Creacion de tabla local
CREATE TABLE local (
    id_local INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL
);

-- Creacion de tabla sala
CREATE TABLE sala (
    id_sala INT AUTO_INCREMENT PRIMARY KEY,
    id_local INT NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL,
    UNIQUE (id_local, nombre),
    FOREIGN KEY (id_local) REFERENCES local(id_local)
);

-- Creación de tabla butaca
CREATE TABLE butaca (
    id_butaca INT AUTO_INCREMENT PRIMARY KEY,
    id_sala INT NOT NULL,
    fila VARCHAR(5) NOT NULL,
    numero INT NOT NULL,
    UNIQUE (id_sala, fila, numero),
    FOREIGN KEY (id_sala) REFERENCES sala(id_sala)
);

-- Creacion de tabla usuario
CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL
);

-- Creacion de tabla pelicula
CREATE TABLE pelicula (
    id_pelicula INT AUTO_INCREMENT PRIMARY KEY,
    id_externo_api VARCHAR(20) UNIQUE,
    titulo VARCHAR(150) NOT NULL,
    sinopsis TEXT NOT NULL,
    poster VARCHAR (100) NOT NULL,
    duracion_minutos VARCHAR (20) NOT NULL,
    clasificacion VARCHAR(20) NOT NULL,
    genero VARCHAR(50) NOT NULL
);

-- Creacion de tabla funcion
CREATE TABLE funcion (
    id_funcion INT AUTO_INCREMENT PRIMARY KEY,
    id_pelicula INT NOT NULL,
    id_sala INT NOT NULL,
    fecha_hora_inicio DATETIME NOT NULL,
    precio_base DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (id_pelicula) REFERENCES pelicula(id_pelicula),
    FOREIGN KEY (id_sala) REFERENCES sala(id_sala)
);

-- Creacion de tabla compra
CREATE TABLE compra (
    id_compra INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULLCHECK (estado IN ('pendiente', 'confirmada', 'expirada', 'cancelada'))
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

-- Creación de tabla entrada
CREATE TABLE entrada (
    id_entrada INT AUTO_INCREMENT PRIMARY KEY,
    id_compra INT NOT NULL,
    id_funcion INT NOT NULL,
    id_butaca INT NOT NULL,
    qr_token VARCHAR(255) NOT NULL UNIQUE,
    fecha_hora_validacion DATETIME,
    UNIQUE (id_funcion, id_butaca),
    FOREIGN KEY (id_compra) REFERENCES compra(id_compra),
    FOREIGN KEY (id_funcion) REFERENCES funcion(id_funcion),
    FOREIGN KEY (id_butaca) REFERENCES butaca(id_butaca)
);

-- Creacion de tabla servicio_adicional
CREATE TABLE servicio_adicional (
    id_servicio INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NOT NULL,
    precio DECIMAL(10,2) NOT NULL
);

-- Creacion de tabla compra_servicio
CREATE TABLE compra_servicio (
    id_compra INT NOT NULL,
    id_servicio INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL, -- la sección 2.12 de las hipótesis ya establece que se conserve el precio cobrado, para que los cambios posteriores no alteren compras anteriores.
    PRIMARY KEY (id_compra, id_servicio),
    FOREIGN KEY (id_compra) REFERENCES compra(id_compra),
    FOREIGN KEY (id_servicio) REFERENCES servicio_adicional(id_servicio)
);

-- JWT cerrados antes de su vencimiento.
-- Ejecutar UNA VEZ sobre la base seleccionada, con permisos CREATE.
-- No elimina tablas ni modifica usuarios o compras existentes.
CREATE TABLE IF NOT EXISTS token_revocado (
    jti CHAR(36) PRIMARY KEY,
    vence_en DATETIME NOT NULL,
    INDEX (vence_en)
);
