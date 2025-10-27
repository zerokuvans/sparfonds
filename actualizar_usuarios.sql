-- Script para actualizar la tabla usuarios con nuevos campos

-- Modificar la tabla usuarios
ALTER TABLE usuarios
  ADD COLUMN cedula VARCHAR(20) NOT NULL UNIQUE,
  ADD COLUMN fecha_nacimiento DATE NOT NULL,
  ADD COLUMN direccion VARCHAR(255) NOT NULL,
  ADD COLUMN telefono VARCHAR(20) NOT NULL;

-- Eliminar el índice si existe
DROP INDEX IF EXISTS idx_cedula ON usuarios;

-- Modificar los tipos de datos de las columnas existentes
ALTER TABLE usuarios
  MODIFY cedula VARCHAR(20),
  MODIFY fecha_nacimiento DATE,
  MODIFY direccion VARCHAR(255),
  MODIFY telefono VARCHAR(20);

-- Agregar restricción UNIQUE a cedula
ALTER TABLE usuarios ADD UNIQUE INDEX idx_cedula (cedula);

-- Crear índice para búsqueda rápida por cédula
CREATE INDEX idx_cedula ON usuarios(cedula);