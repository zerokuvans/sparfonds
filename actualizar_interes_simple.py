# Script para actualizar la base de datos con el nuevo sistema de interés simple
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

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def actualizar_base_datos():
    print("Iniciando actualización para sistema de interés simple anualizado...")
    
    conn = get_db_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Verificar si las columnas ya existen
        cursor.execute("SHOW COLUMNS FROM prestamos LIKE 'interes_mensual_fijo'")
        if not cursor.fetchone():
            print("Agregando columna interes_mensual_fijo...")
            cursor.execute("ALTER TABLE prestamos ADD COLUMN interes_mensual_fijo DECIMAL(10, 2) DEFAULT NULL COMMENT 'Interés mensual fijo calculado sobre el monto inicial'")
            print("✓ Columna interes_mensual_fijo agregada")
        else:
            print("✓ Columna interes_mensual_fijo ya existe")
        
        cursor.execute("SHOW COLUMNS FROM prestamos LIKE 'cuota_capital_mensual'")
        if not cursor.fetchone():
            print("Agregando columna cuota_capital_mensual...")
            cursor.execute("ALTER TABLE prestamos ADD COLUMN cuota_capital_mensual DECIMAL(10, 2) DEFAULT NULL COMMENT 'Cuota de capital mensual (monto/plazo)'")
            print("✓ Columna cuota_capital_mensual agregada")
        else:
            print("✓ Columna cuota_capital_mensual ya existe")
        
        # Crear índices
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prestamos_estado ON prestamos(estado)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prestamos_usuario_estado ON prestamos(usuario_id, estado)")
            print("✓ Índices creados")
        except mysql.connector.Error as e:
            if "Duplicate key name" not in str(e):
                print(f"Advertencia al crear índices: {e}")
        
        conn.commit()
        print("\n✅ Actualización de base de datos completada exitosamente")
        
        # Actualizar préstamos existentes aprobados con el nuevo cálculo
        print("\nActualizando préstamos existentes...")
        cursor.execute("SELECT id, monto, tasa_interes, plazo_meses FROM prestamos WHERE estado = 'aprobado' AND tasa_interes IS NOT NULL AND plazo_meses IS NOT NULL")
        prestamos = cursor.fetchall()
        
        for prestamo in prestamos:
            prestamo_id, monto, tasa_interes, plazo_meses = prestamo
            
            # Calcular interés mensual fijo: (monto * tasa_anual) / 12
            interes_anual = float(monto) * (float(tasa_interes) / 100)
            interes_mensual_fijo = interes_anual / 12
            
            # Calcular cuota de capital mensual: monto / plazo
            cuota_capital_mensual = float(monto) / plazo_meses
            
            # Actualizar el préstamo
            cursor.execute("""
                UPDATE prestamos 
                SET interes_mensual_fijo = %s, cuota_capital_mensual = %s 
                WHERE id = %s
            """, (interes_mensual_fijo, cuota_capital_mensual, prestamo_id))
            
            print(f"✓ Préstamo #{prestamo_id}: Interés mensual fijo ${interes_mensual_fijo:.2f}, Cuota capital ${cuota_capital_mensual:.2f}")
        
        conn.commit()
        print(f"\n✅ Se actualizaron {len(prestamos)} préstamos existentes")
        
    except mysql.connector.Error as err:
        print(f"Error durante la actualización: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

if __name__ == "__main__":
    if actualizar_base_datos():
        print("\n🎉 ¡Actualización completada! El sistema ahora usa interés simple anualizado.")
        print("\nCaracterísticas del nuevo sistema:")
        print("- Interés fijo mensual sobre el monto inicial")
        print("- Cuota de capital fija (monto/plazo)")
        print("- Cada pago = cuota_capital + interés_fijo")
    else:
        print("\n❌ Error durante la actualización")
        sys.exit(1)