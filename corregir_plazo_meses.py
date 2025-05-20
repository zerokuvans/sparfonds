import mysql.connector
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la base de datos MySQL desde variables de entorno
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sparfonds')
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def corregir_plazo_meses():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        try:
            # Modificar la columna plazo_meses para permitir valores NULL
            print("Modificando la columna plazo_meses para permitir valores NULL...")
            cursor.execute("ALTER TABLE prestamos MODIFY COLUMN plazo_meses INT NULL;")
            
            # Actualizar los préstamos pendientes existentes para tener plazo_meses = NULL
            print("Actualizando préstamos pendientes existentes...")
            cursor.execute("UPDATE prestamos SET plazo_meses = NULL WHERE estado = 'pendiente' AND plazo_meses IS NOT NULL;")
            
            conn.commit()
            print("¡Corrección completada con éxito!")
            print("Ahora puede insertar nuevos préstamos sin especificar un valor para plazo_meses.")
            print("El plazo se establecerá cuando el administrador apruebe el préstamo.")
            
        except mysql.connector.Error as err:
            print(f"Error al corregir la base de datos: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    else:
        print("No se pudo conectar a la base de datos.")

if __name__ == "__main__":
    corregir_plazo_meses()