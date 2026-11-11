-- Seleccionar antes la base de destino con USE.
-- Puede repetirse y conserva las rutas de imágenes ya cargadas.
DROP PROCEDURE IF EXISTS migrar_imagen_servicios;
DELIMITER //
CREATE PROCEDURE migrar_imagen_servicios()
BEGIN
    IF DATABASE() IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seleccionar una base antes de migrar';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'servicio_adicional'
          AND COLUMN_NAME = 'imagen'
    ) THEN
        ALTER TABLE servicio_adicional ADD COLUMN imagen VARCHAR(255) NOT NULL DEFAULT '';
    ELSE
        UPDATE servicio_adicional SET imagen = '' WHERE imagen IS NULL;
        ALTER TABLE servicio_adicional MODIFY COLUMN imagen VARCHAR(255) NOT NULL DEFAULT '';
    END IF;
END//
DELIMITER ;
CALL migrar_imagen_servicios();
DROP PROCEDURE migrar_imagen_servicios;
