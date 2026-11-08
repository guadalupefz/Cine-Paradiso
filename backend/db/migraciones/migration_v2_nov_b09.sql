-- Unificación de Estados y Limpieza de Reservas
USE cine_paradiso;

-- 1. Unificar el estado legado 'aprobada' al estado oficial 'confirmada'
UPDATE compra 
SET estado = 'confirmada' 
WHERE LOWER(estado) = 'aprobada';

-- 2. Expirar compras pendientes que superaron la ventana de 15 minutos
UPDATE compra 
SET estado = 'expirada' 
WHERE estado = 'pendiente' 
  AND fecha_hora &lt;= NOW() - INTERVAL 15 MINUTE;

-- 3. Liberar asientos: eliminar las entradas asociadas a compras expiradas
DELETE e 
FROM entrada e
INNER JOIN compra c ON c.id_compra = e.id_compra
WHERE c.estado = 'expirada';