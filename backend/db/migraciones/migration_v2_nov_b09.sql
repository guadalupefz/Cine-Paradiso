USE cine_paradiso;

DROP PROCEDURE IF EXISTS migrar_nov_b09;
DELIMITER //
CREATE PROCEDURE migrar_nov_b09()
BEGIN
    DECLARE nombre_check VARCHAR(64) DEFAULT NULL;

    IF EXISTS (
        SELECT 1
        FROM pelicula
        WHERE CAST(duracion_minutos AS CHAR)
                  NOT REGEXP '^[[:space:]]*[0-9]+([[:space:]]*min)?[[:space:]]*$'
           OR CAST(
                  REGEXP_SUBSTR(CAST(duracion_minutos AS CHAR), '[0-9]+')
                  AS UNSIGNED
              ) NOT BETWEEN 1 AND 1440
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Hay duraciones inválidas en pelicula.duracion_minutos';
    END IF;

    UPDATE pelicula
    SET duracion_minutos = CAST(
        REGEXP_SUBSTR(CAST(duracion_minutos AS CHAR), '[0-9]+')
        AS UNSIGNED
    );

    ALTER TABLE pelicula
        MODIFY duracion_minutos INT NOT NULL;

    UPDATE compra
    SET estado = 'confirmada'
    WHERE LOWER(estado) = 'aprobada';

    UPDATE compra
    SET estado = 'expirada'
    WHERE estado = 'pendiente'
      AND fecha_hora <= NOW() - INTERVAL 15 MINUTE;

    SELECT CONSTRAINT_NAME
    INTO nombre_check
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND TABLE_NAME = 'compra'
      AND CONSTRAINT_TYPE = 'CHECK'
    LIMIT 1;

    IF nombre_check IS NOT NULL THEN
        SET @sql_drop_check = CONCAT(
            'ALTER TABLE compra DROP CHECK `',
            REPLACE(nombre_check, '`', '``'),
            '`'
        );
        PREPARE sentencia_drop_check FROM @sql_drop_check;
        EXECUTE sentencia_drop_check;
        DEALLOCATE PREPARE sentencia_drop_check;
    END IF;

    ALTER TABLE compra
        ADD CONSTRAINT chk_compra_estado CHECK (
            estado IN (
                'pendiente',
                'confirmada',
                'expirada',
                'cancelada',
                'rechazada'
            )
        );

    UPDATE entrada
    JOIN compra ON entrada.id_compra = compra.id_compra
    SET entrada.ocupacion_activa = NULL
    WHERE compra.estado IN ('cancelada', 'expirada');
END//
DELIMITER ;

CALL migrar_nov_b09();
DROP PROCEDURE migrar_nov_b09;