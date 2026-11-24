-- Seleccionar antes la base de destino con USE.
-- Conserva los servicios existentes y puede ejecutarse más de una vez.
DROP PROCEDURE IF EXISTS migrar_descripcion_servicios;
DELIMITER //
CREATE PROCEDURE migrar_descripcion_servicios()
BEGIN
    IF DATABASE() IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seleccionar una base antes de migrar';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'servicio_adicional'
          AND COLUMN_NAME = 'descripcion'
    ) THEN
        ALTER TABLE servicio_adicional
            ADD COLUMN descripcion VARCHAR(255) NOT NULL DEFAULT '' AFTER nombre;
    END IF;

    UPDATE servicio_adicional
    SET descripcion = nombre
    WHERE descripcion IS NULL OR TRIM(descripcion) = '';
END//
DELIMITER ;
CALL migrar_descripcion_servicios();
DROP PROCEDURE migrar_descripcion_servicios;
