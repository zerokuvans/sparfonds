-- Script para actualizar el sistema de préstamos a interés simple anualizado

-- Agregar columna para almacenar el interés mensual fijo
ALTER TABLE prestamos ADD COLUMN interes_mensual_fijo DECIMAL(10, 2) DEFAULT NULL COMMENT 'Interés mensual fijo calculado sobre el monto inicial';

-- Agregar columna para almacenar el monto de capital mensual
ALTER TABLE prestamos ADD COLUMN cuota_capital_mensual DECIMAL(10, 2) DEFAULT NULL COMMENT 'Cuota de capital mensual (monto/plazo)';

-- Agregar índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_prestamos_estado ON prestamos(estado);
CREATE INDEX IF NOT EXISTS idx_prestamos_usuario_estado ON prestamos(usuario_id, estado);