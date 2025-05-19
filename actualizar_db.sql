-- Script para actualizar la estructura de la base de datos

-- Añadir la columna 'rol' a la tabla usuarios si no existe
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol ENUM('admin', 'ahorrador') DEFAULT 'ahorrador';

-- Actualizar usuarios existentes para asignarles el rol 'ahorrador' por defecto
UPDATE usuarios SET rol = 'ahorrador' WHERE rol IS NULL;

-- Verificar si existe un usuario administrador, si no, crearlo
-- Este paso se realizará desde el código Python