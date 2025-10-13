#!/usr/bin/env python3
"""
Generador de SECRET_KEY segura para SPARFONDS
Ejecuta este script para generar nuevas claves criptográficamente seguras
"""

import secrets
import sys

def generar_secret_key(longitud=32):
    """
    Genera una SECRET_KEY segura
    
    Args:
        longitud (int): Longitud en bytes (el resultado será el doble en hex)
    
    Returns:
        str: SECRET_KEY en formato hexadecimal
    """
    return secrets.token_hex(longitud)

def main():
    print("🔐 GENERADOR DE SECRET_KEY PARA SPARFONDS")
    print("=" * 50)
    print()
    
    # Generar clave principal recomendada
    secret_key = generar_secret_key(32)  # 64 caracteres hex
    
    print(f"SECRET_KEY RECOMENDADA:")
    print(f"{secret_key}")
    print(f"Longitud: {len(secret_key)} caracteres")
    print()
    
    # Generar alternativas
    print("ALTERNATIVAS:")
    print(f"Opción 1 (64 chars): {generar_secret_key(32)}")
    print(f"Opción 2 (48 chars): {generar_secret_key(24)}")
    print(f"Opción 3 (32 chars): {generar_secret_key(16)}")
    print()
    
    # Generar usando token_urlsafe (más compacto)
    print("FORMATO URL-SAFE (más compacto):")
    print(f"URL-Safe 32 chars: {secrets.token_urlsafe(24)}")
    print(f"URL-Safe 43 chars: {secrets.token_urlsafe(32)}")
    print()
    
    print("📋 INSTRUCCIONES:")
    print("1. Copia una de las claves generadas arriba")
    print("2. Pégala en tu archivo .env como:")
    print("   SECRET_KEY=tu_clave_aqui")
    print("3. Reinicia tu aplicación")
    print()
    
    print("⚠️  IMPORTANTE:")
    print("• NUNCA compartas esta clave públicamente")
    print("• Usa claves diferentes para desarrollo y producción")
    print("• Guarda la clave en un lugar seguro")
    print("• Si cambias la clave, todos los usuarios deberán hacer login nuevamente")

if __name__ == "__main__":
    main()