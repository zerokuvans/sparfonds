# Configuración de SSL para la aplicación SparFonds
import os
import ssl

# Función para verificar si los certificados SSL existen
def certificados_ssl_existen():
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificates")
    cert_path = os.path.join(cert_dir, "cert.pem")
    key_path = os.path.join(cert_dir, "key.pem")
    return os.path.exists(cert_path) and os.path.exists(key_path)

# Función para obtener las rutas de los certificados SSL
def obtener_rutas_certificados():
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificates")
    return {
        'cert': os.path.join(cert_dir, "cert.pem"),
        'key': os.path.join(cert_dir, "key.pem")
    }

# Función para crear contexto SSL
def crear_contexto_ssl():
    if not certificados_ssl_existen():
        return None
        
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    certificados = obtener_rutas_certificados()
    context.load_cert_chain(certificados['cert'], certificados['key'])
    return context

# Configuración para entorno de producción
def configurar_seguridad_produccion(app):
    # Configurar cookies seguras en producción
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # Configurar cabeceras de seguridad
    @app.after_request
    def aplicar_cabeceras_seguridad(response):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
    
    return app