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

-- Liberar las butacas sin eliminar el historial de entradas
UPDATE entrada
JOIN compra ON entrada.id_compra = compra.id_compra
SET entrada.ocupacion_activa = NULL
WHERE compra.estado IN ('cancelada', 'expirada');