import os
from dotenv import load_dotenv

# Cargar el archivo .env.production
load_dotenv('.env.production')

print('=== VERIFICACION DE SECRET_KEY ===')
print()

secret_key = os.getenv('SECRET_KEY')
if secret_key:
    print('✓ SECRET_KEY configurada')
    print(f'  Longitud: {len(secret_key)} caracteres')
    print(f'  Primeros 10 chars: {secret_key[:10]}...')
    print(f'  Ultimos 10 chars: ...{secret_key[-10:]}')
    
    # Verificar que no sea la clave de ejemplo
    if 'tu-clave-secreta' in secret_key or 'cambiar-en-produccion' in secret_key:
        print('⚠️  ADVERTENCIA: Aun tienes la clave de ejemplo!')
    else:
        print('✓ SECRET_KEY parece ser segura')
else:
    print('✗ SECRET_KEY no encontrada')

print()
print('Otras configuraciones:')
print('FLASK_ENV:', os.getenv('FLASK_ENV'))
print('FORCE_HTTPS:', os.getenv('FORCE_HTTPS'))
print('HTTPS:', os.getenv('HTTPS'))