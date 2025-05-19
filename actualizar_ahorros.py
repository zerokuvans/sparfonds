# Script para actualizar la tabla ahorros y añadir la columna 'validado'
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
    print("Iniciando proceso de actualización de la tabla ahorros...")
    
    # Paso 1: Verificar la conexión a la base de datos
    conn = get_db_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return False
    
    print("Conexión a la base de datos establecida correctamente.")
    
    # Paso 2: Verificar si la columna 'validado' existe en la tabla ahorros
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW COLUMNS FROM ahorros LIKE 'validado'")
        column_exists = cursor.fetchone()
        
        if column_exists:
            print("La columna 'validado' ya existe en la tabla ahorros.")
        else:
            print("La columna 'validado' no existe. Añadiendo columna...")
            cursor.execute("ALTER TABLE ahorros ADD COLUMN validado BOOLEAN DEFAULT 0")
            conn.commit()
            print("Columna 'validado' añadida correctamente.")
            
            # Actualizar registros existentes
            cursor.execute("UPDATE ahorros SET validado = 0 WHERE validado IS NULL")
            conn.commit()
            print("Registros existentes actualizados.")
        
        print("\nProceso de actualización completado.")
        print("\nPuede iniciar la aplicación normalmente con 'python app.py'")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error al actualizar la base de datos: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    ejecutar_actualizacion()