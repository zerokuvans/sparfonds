-- Script para actualizar la estructura de la tabla pagos_prestamos

-- Asegurar que la tabla pagos_prestamos existe
CREATE TABLE IF NOT EXISTS pagos_prestamos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prestamo_id INT NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
);

-- Añadir un índice para mejorar el rendimiento de las consultas
CREATE INDEX IF NOT EXISTS idx_prestamo_id ON pagos_prestamos(prestamo_id);