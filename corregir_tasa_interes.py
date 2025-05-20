# Script para corregir el problema con el campo tasa_interes en la tabla préstamos
import mysql.connector
import os
import sys

# Configuración de la base de datos MySQL
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '732137A031E4b@'),
    'database': os.getenv('DB_NAME', 'sparfonds')
}

def corregir_tasa_interes():
    print("Iniciando corrección del campo tasa_interes en la tabla préstamos...")
    
    # Conectar a la base de datos
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        print("Conexión a la base de datos establecida correctamente.")
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return False
    
    try:
        # Verificar si la columna tasa_interes permite valores NULL
        cursor.execute("SHOW COLUMNS FROM prestamos LIKE 'tasa_interes'")
        column_info = cursor.fetchone()
        
        if column_info and 'NO' in column_info['Null']:  # 'NO' indica que no permite NULL
            print("Modificando la columna tasa_interes para permitir valores NULL...")
            cursor.execute("ALTER TABLE prestamos MODIFY COLUMN tasa_interes DECIMAL(5, 2) NULL")
            conn.commit()
            print("Columna tasa_interes modificada correctamente.")
            
            # Actualizar préstamos pendientes para establecer tasa_interes como NULL
            cursor.execute("UPDATE prestamos SET tasa_interes = NULL WHERE estado = 'pendiente'")
            conn.commit()
            print(f"Se actualizaron {cursor.rowcount} préstamos pendientes para tener tasa_interes NULL.")
        else:
            print("La columna tasa_interes ya permite valores NULL.")
            
        print("\nCorrección completada. Ahora puede ejecutar la aplicación sin problemas.")
        print("Recuerde que los préstamos pendientes no tendrán tasa de interés hasta que sean aprobados.")
        return True
    
    except mysql.connector.Error as err:
        print(f"Error al actualizar la base de datos: {err}")
        return False
    finally:
        cursor.close()
        conn.close()

def mostrar_ayuda():
    print("\nUso: python corregir_tasa_interes.py [opciones]")
    print("Opciones:")
    print("  --help    Muestra esta ayuda")
    print("\nEste script corrige el problema con el campo tasa_interes en la tabla préstamos")
    print("permitiendo valores NULL para préstamos pendientes.")

if __name__ == "__main__":
    if "--help" in sys.argv:
        mostrar_ayuda()
    else:
        corregir_tasa_interes()