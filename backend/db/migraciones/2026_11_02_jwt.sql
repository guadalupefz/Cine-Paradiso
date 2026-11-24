-- Ejecutar UNA VEZ sobre la base seleccionada, con permisos CREATE.
-- No elimina tablas ni modifica usuarios o compras existentes.
CREATE TABLE IF NOT EXISTS token_revocado (
    jti CHAR(36) PRIMARY KEY,
    vence_en DATETIME NOT NULL,
    INDEX (vence_en)
);
