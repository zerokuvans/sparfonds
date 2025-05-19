-- Script para actualizar la estructura de la tabla préstamos

-- Modificar la columna 'tasa_interes' para permitir valores NULL
ALTER TABLE prestamos MODIFY COLUMN tasa_interes DECIMAL(5, 2) NULL;

-- Actualizar préstamos pendientes para establecer tasa_interes como NULL
UPDATE prestamos SET tasa_interes = NULL WHERE estado = 'pendiente';