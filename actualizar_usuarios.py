import mysql.connector
import sys
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

def conectar_bd():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

def actualizar_tabla_usuarios():
    conn = conectar_bd()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Leer y ejecutar el script SQL
            with open('actualizar_usuarios.sql', 'r') as file:
                sql_commands = file.read().split(';')
                
                for command in sql_commands:
                    if command.strip():
                        print(f"Ejecutando: {command}")
                        cursor.execute(command)
                        conn.commit()
            
            print("Actualización de la tabla usuarios completada con éxito.")
            
        except mysql.connector.Error as err:
            print(f"Error al actualizar la tabla usuarios: {err}")
        except Exception as e:
            print(f"Error al leer o ejecutar el script SQL: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    actualizar_tabla_usuarios()