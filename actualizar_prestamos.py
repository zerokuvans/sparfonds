# Script para actualizar la tabla préstamos y modificar la funcionalidad de aprobación
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
    print("Iniciando proceso de actualización de la tabla préstamos...")
    
    # Paso 1: Verificar la conexión a la base de datos
    conn = get_db_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return False
    
    print("Conexión a la base de datos establecida correctamente.")
    
    # Paso 2: Modificar la tabla préstamos para hacer que tasa_interes sea NULL por defecto
    cursor = conn.cursor()
    try:
        # Verificar si la columna tasa_interes permite valores NULL
        cursor.execute("SHOW COLUMNS FROM prestamos LIKE 'tasa_interes'")
        column_info = cursor.fetchone()
        
        if column_info and 'NO' in column_info[2]:  # 'NO' indica que no permite NULL
            print("Modificando la columna tasa_interes para permitir valores NULL...")
            cursor.execute("ALTER TABLE prestamos MODIFY COLUMN tasa_interes DECIMAL(5, 2) NULL")
            conn.commit()
            print("Columna tasa_interes modificada correctamente.")
        else:
            print("La columna tasa_interes ya permite valores NULL.")
        
        # Verificar si existe la ruta para validar préstamos con tasa de interés
        print("\nActualización de la tabla préstamos completada.")
        print("\nAhora debe actualizar los archivos de la aplicación:")
        print("1. Modificar el formulario en templates/prestamos.html para eliminar el campo de tasa de interés")
        print("2. Actualizar la ruta /prestamos en app.py para no requerir tasa_interes")
        print("3. Modificar la ruta /validar_prestamo en app.py para incluir la tasa de interés")
        print("4. Actualizar la plantilla admin.html para incluir un campo de tasa de interés al aprobar")
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