# Configuración de Sesiones para Producción - SPARFONDS

## Problema Resuelto
Se ha corregido el problema de pérdida de sesiones en producción donde los usuarios eran redirigidos al login después de navegar a otras vistas.

## Cambios Implementados

### 1. Secret Key Estable
- **Antes**: `app.secret_key = os.urandom(24)` (generaba una clave diferente en cada reinicio)
- **Ahora**: Secret key estable desde variable de entorno o clave fija para desarrollo

### 2. Configuración de Sesiones Mejorada
```python
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora
app.config['SESSION_COOKIE_NAME'] = 'sparfonds_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### 3. Detección Automática de Producción
La aplicación detecta automáticamente si está en producción basándose en:
- `FLASK_ENV=production`
- `HTTPS=on`
- `FORCE_HTTPS=true`

### 4. Configuración de Cookies Seguras
En producción se configuran automáticamente:
- `SESSION_COOKIE_SECURE = True` (solo HTTPS)
- `PREFERRED_URL_SCHEME = 'https'`

### 5. Sesiones Permanentes
- Las sesiones se configuran como permanentes en el login
- Se renuevan automáticamente en cada request autenticado

## Configuración para Producción

### Paso 1: Variables de Entorno
Crea un archivo `.env` en producción con:

```bash
# Configuración de Flask
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-super-segura-aqui-cambiar-en-produccion
FORCE_HTTPS=true

# Configuración de base de datos
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu-password-de-base-de-datos
DB_NAME=sparfonds

# Configuración HTTPS
HTTPS=on
```

### Paso 2: Generar Secret Key Segura
Para generar una secret key segura, ejecuta:

```python
import secrets
print(secrets.token_hex(32))
```

### Paso 3: Verificar Configuración
Ejecuta el script de verificación:

```bash
python check_config.py
```

Deberías ver:
```
=== CONFIGURACION DE SESIONES ===
SECRET_KEY configurado: True
PERMANENT_SESSION_LIFETIME: 3600
SESSION_COOKIE_NAME: sparfonds_session
SESSION_COOKIE_SECURE: True  # En producción
SESSION_COOKIE_HTTPONLY: True
PREFERRED_URL_SCHEME: https  # En producción
Es produccion: True  # En producción
```

## Debugging en Producción

### Logs Agregados
Se han agregado logs para debugging:
- Login exitoso: muestra email y session ID
- Pérdida de sesión: muestra desde qué endpoint se redirige

### Verificar Logs
Busca en los logs del servidor:
```
Usuario usuario@email.com logueado exitosamente. Session ID: 123
Sesión no encontrada. Redirigiendo a login desde: ahorros
```

## Solución de Problemas

### Si las sesiones siguen perdiéndose:

1. **Verificar HTTPS**: Asegúrate de que el sitio esté corriendo en HTTPS
2. **Verificar Secret Key**: Debe ser la misma en todos los procesos/servidores
3. **Verificar Variables de Entorno**: `FLASK_ENV=production` o `FORCE_HTTPS=true`
4. **Verificar Cookies**: Usar herramientas de desarrollador para ver las cookies

### Comandos de Verificación:

```bash
# Verificar configuración actual
python check_config.py

# Verificar variables de entorno
echo $FLASK_ENV
echo $SECRET_KEY
echo $HTTPS

# Verificar logs de la aplicación
tail -f /var/log/sparfonds/app.log
```

## Notas Importantes

1. **Secret Key**: NUNCA uses la clave de desarrollo en producción
2. **HTTPS**: Las cookies seguras solo funcionan con HTTPS
3. **Dominio**: Si usas múltiples subdominios, configura `SESSION_COOKIE_DOMAIN`
4. **Load Balancer**: Si usas múltiples servidores, todos deben tener la misma secret key

## Archivos Modificados

- `app.py`: Configuración principal de sesiones
- `ssl_config.py`: Configuración de seguridad mejorada
- `.env.production`: Plantilla de configuración para producción
- `check_config.py`: Script de verificación

El problema de pérdida de sesiones en producción ha sido resuelto con estas configuraciones.