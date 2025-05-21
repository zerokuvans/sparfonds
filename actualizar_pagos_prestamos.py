# Script para actualizar la tabla pagos_prestamos y añadir funcionalidad de registro de pagos
import mysql.connector
import sys
import os

# Configuración de la base de datos MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '732137A031E4b@',
    'database': 'sparfonds'
}

# Función para conectar a la base de datos
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def ejecutar_actualizacion():
    print("Iniciando proceso de actualización para el historial de pagos de préstamos...")
    
    # Paso 1: Verificar la conexión a la base de datos
    conn = get_db_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return False
    
    print("Conexión a la base de datos establecida correctamente.")
    
    # Paso 2: Ejecutar el script SQL para actualizar la estructura de la tabla
    cursor = conn.cursor()
    try:
        # Verificar si la tabla pagos_prestamos existe
        cursor.execute("SHOW TABLES LIKE 'pagos_prestamos'")
        tabla_existe = cursor.fetchone()
        
        if not tabla_existe:
            print("Creando tabla pagos_prestamos...")
            cursor.execute("""
            CREATE TABLE pagos_prestamos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                prestamo_id INT NOT NULL,
                monto DECIMAL(10, 2) NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
            )
            """)
            print("Tabla pagos_prestamos creada correctamente.")
        else:
            print("La tabla pagos_prestamos ya existe.")
        
        # Crear índice para mejorar el rendimiento
        try:
            cursor.execute("CREATE INDEX idx_prestamo_id ON pagos_prestamos(prestamo_id)")
            print("Índice idx_prestamo_id creado correctamente.")
        except mysql.connector.Error as err:
            if err.errno == 1061:  # Error de índice duplicado
                print("El índice idx_prestamo_id ya existe.")
            else:
                print(f"Error al crear índice: {err}")
        
        conn.commit()
        print("\nActualización de la tabla pagos_prestamos completada.")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error al actualizar la base de datos: {err}")
        conn.rollback()
        return False
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if ejecutar_actualizacion():
        print("\nLa actualización se completó correctamente.")
        print("Ahora puede registrar pagos de préstamos y ver el historial de pagos con saldo restante.")
    else:
        print("\nLa actualización falló. Por favor revise los errores e intente nuevamente.")