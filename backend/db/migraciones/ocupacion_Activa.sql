-- Liberar butacas canceladas conservando historial
ALTER TABLE entrada
ADD COLUMN ocupacion_activa BOOLEAN NULL DEFAULT TRUE;

-- Liberar las entradas de compras canceladas o expiradas
UPDATE entrada
JOIN compra ON entrada.id_compra = compra.id_compra
SET entrada.ocupacion_activa = NULL
WHERE compra.estado IN ('cancelada', 'expirada');

-- Permitir una sola ocupacion activa por butaca y funcion
ALTER TABLE entrada
ADD UNIQUE KEY uq_entrada_ocupacion_activa (
    id_funcion,
    id_butaca,
    ocupacion_activa
);

ALTER TABLE entrada
DROP INDEX id_funcion;