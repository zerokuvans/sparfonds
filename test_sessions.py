#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de sesiones en SPARFONDS
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_session_config():
    """Prueba la configuración de sesiones"""
    print("=== PRUEBA DE CONFIGURACIÓN DE SESIONES ===\n")
    
    # Importar la aplicación
    try:
        from app import app
        print("✓ Aplicación importada correctamente")
    except Exception as e:
        print(f"✗ Error al importar la aplicación: {e}")
        return False
    
    # Verificar configuración de sesiones
    print("\n--- Configuración de Sesiones ---")
    
    configs_to_check = [
        'SECRET_KEY',
        'PERMANENT_SESSION_LIFETIME',
        'SESSION_COOKIE_NAME',
        'SESSION_COOKIE_HTTPONLY',
        'SESSION_COOKIE_SAMESITE',
        'SESSION_COOKIE_SECURE',
        'PREFERRED_URL_SCHEME'
    ]
    
    for config in configs_to_check:
        value = app.config.get(config, 'NO CONFIGURADO')
        print(f"{config}: {value}")
    
    # Verificar variables de entorno
    print("\n--- Variables de Entorno ---")
    env_vars = [
        'FLASK_ENV',
        'SECRET_KEY',
        'FORCE_HTTPS',
        'HTTPS'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NO CONFIGURADO')
        print(f"{var}: {value}")
    
    # Verificar detección de producción
    print("\n--- Detección de Entorno ---")
    try:
        from app import is_production_environment
        is_prod = is_production_environment()
        print(f"¿Es producción?: {is_prod}")
    except Exception as e:
        print(f"Error al verificar entorno: {e}")
    
    print("\n=== PRUEBA COMPLETADA ===")
    return True

if __name__ == "__main__":
    test_session_config()