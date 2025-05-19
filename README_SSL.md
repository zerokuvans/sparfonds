# Configuración de SSL/TLS para SparFonds

## Introducción

Este documento explica cómo se ha implementado la protección HTTPS con SSL/TLS en la aplicación SparFonds y cómo configurarla correctamente tanto en entornos de desarrollo como de producción.

## Entorno de Desarrollo

### Generación de Certificados Autofirmados

Para el entorno de desarrollo, se utilizan certificados autofirmados. Siga estos pasos para generarlos:

1. Asegúrese de tener OpenSSL instalado en su sistema
2. Ejecute el script de generación de certificados:

```
python generar_certificados.py
```

Esto creará un directorio `certificates` con los archivos `cert.pem` y `key.pem`.

### Ejecución con SSL en Desarrollo

Una vez generados los certificados, la aplicación detectará automáticamente su presencia y se ejecutará con soporte SSL:

```
python app.py
```

La aplicación estará disponible en `https://localhost:8080`

> **Nota**: Como los certificados son autofirmados, su navegador mostrará una advertencia de seguridad. Esto es normal en entornos de desarrollo.

## Entorno de Producción

En producción, debe utilizar certificados emitidos por una Autoridad Certificadora (CA) confiable como Let's Encrypt, DigiCert, etc.

### Configuración en Producción

1. Obtenga certificados válidos de una CA reconocida
2. Coloque los archivos de certificado y clave en el directorio `certificates` con los nombres `cert.pem` y `key.pem` respectivamente
3. Configure la variable de entorno para indicar que está en producción:

```
set FLASK_ENV=production  # En Windows
# o
export FLASK_ENV=production  # En Linux/Mac
```

4. Inicie la aplicación:

```
python app.py
```

### Características de Seguridad Implementadas

- Redirección automática de HTTP a HTTPS en producción
- Cookies seguras (con flags secure y httponly)
- Cabeceras de seguridad (HSTS, X-Content-Type-Options, etc.)
- Configuración TLS moderna y segura

## Verificación de la Configuración SSL

Para verificar que su configuración SSL es segura, puede utilizar herramientas como:

- [SSL Labs Server Test](https://www.ssllabs.com/ssltest/)
- [Mozilla Observatory](https://observatory.mozilla.org/)

## Solución de Problemas

### La aplicación no inicia con SSL

Verifique que:

1. Los certificados existen en el directorio `certificates`
2. Los archivos tienen los nombres correctos (`cert.pem` y `key.pem`)
3. Los permisos de los archivos son adecuados

### Errores de certificado en el navegador

- En desarrollo: Es normal recibir advertencias con certificados autofirmados
- En producción: Verifique que sus certificados son válidos y emitidos por una CA reconocida

## Recomendaciones Adicionales

- Renueve sus certificados antes de que expiren
- Mantenga actualizada la biblioteca SSL de su sistema
- Configure correctamente su firewall para permitir tráfico HTTPS (puerto 443)
- Considere utilizar un proxy inverso como Nginx para manejar SSL en producción