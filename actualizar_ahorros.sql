-- Script para actualizar la estructura de la tabla ahorros

-- Añadir la columna 'validado' a la tabla ahorros si no existe
ALTER TABLE ahorros ADD COLUMN IF NOT EXISTS validado BOOLEAN DEFAULT 0;

-- Actualizar registros existentes para asignarles validado = 0 por defecto
UPDATE ahorros SET validado = 0 WHERE validado IS NULL;