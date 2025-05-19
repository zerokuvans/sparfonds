# Script para actualizar la base de datos y probar la solución
import mysql.connector
import sys
import os

# Añadir el directorio actual al path para poder importar desde app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar las funciones necesarias desde app.py
from app import get_db_connection, setup_database, crear_admin_inicial

def ejecutar_actualizacion():
    print("Iniciando proceso de actualización de la base de datos...")
    
    # Paso 1: Verificar la conexión a la base de datos
    conn = get_db_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return False
    
    print("Conexión a la base de datos establecida correctamente.")
    
    # Paso 2: Ejecutar la función de configuración de la base de datos
    print("Configurando la estructura de la base de datos...")
    setup_database()
    
    # Paso 3: Ejecutar la función para crear el administrador inicial
    print("Verificando/creando usuario administrador...")
    crear_admin_inicial()
    
    print("\nProceso de actualización completado.")
    print("\nPuede iniciar la aplicación normalmente con 'python app.py'")
    return True

if __name__ == "__main__":
    ejecutar_actualizacion()