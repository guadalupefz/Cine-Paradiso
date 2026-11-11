-- Migración: Agregar columna imagen a servicio_adicional
-- Fecha: 2026-11-11

USE cine_paradiso;

ALTER TABLE servicio_adicional 
ADD COLUMN imagen VARCHAR(255) DEFAULT NULL;