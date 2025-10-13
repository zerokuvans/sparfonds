import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app import app, is_production_environment
    print('=== CONFIGURACION DE SESIONES ===')
    print('SECRET_KEY configurado:', bool(app.secret_key))
    print('PERMANENT_SESSION_LIFETIME:', app.config.get('PERMANENT_SESSION_LIFETIME'))
    print('SESSION_COOKIE_NAME:', app.config.get('SESSION_COOKIE_NAME'))
    print('SESSION_COOKIE_SECURE:', app.config.get('SESSION_COOKIE_SECURE'))
    print('SESSION_COOKIE_HTTPONLY:', app.config.get('SESSION_COOKIE_HTTPONLY'))
    print('PREFERRED_URL_SCHEME:', app.config.get('PREFERRED_URL_SCHEME'))
    print('Es produccion:', is_production_environment())
    print('Configuracion cargada correctamente')
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()