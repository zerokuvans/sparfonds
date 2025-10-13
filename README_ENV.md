# Configuración de Variables de Entorno para SparFonds

## Introducción

Este documento explica cómo configurar las variables de entorno para la aplicación SparFonds, lo que mejora la seguridad al separar las credenciales sensibles del código fuente.

## Configuración

1. Crea un archivo `.env` en el directorio raíz del proyecto (ya existe un archivo `.env.example` como plantilla)
2. Configura las siguientes variables en el archivo `.env`:

```
# Configuración de la base de datos
DB_HOST=localhost
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_NAME=sparfonds

# Configuración de la aplicación
FLASK_ENV=development
# Cambiar a 'production' en entorno de producción
```

## Importancia de la Seguridad

El uso de variables de entorno para almacenar credenciales sensibles es una práctica recomendada de seguridad por las siguientes razones:

- **Separación de configuración y código**: Mantiene las credenciales fuera del código fuente
- **Prevención de exposición**: Evita que las credenciales se suban a repositorios de control de versiones
- **Flexibilidad**: Permite diferentes configuraciones para distintos entornos (desarrollo, pruebas, producción)

## Notas Importantes

- El archivo `.env` está incluido en `.gitignore` para evitar que se suba al repositorio
- Nunca compartas tu archivo `.env` con credenciales reales
- Para despliegues, configura las variables de entorno directamente en el servidor o plataforma de hosting

## Dependencias

Esta funcionalidad utiliza la biblioteca `python-dotenv` que ya está incluida en el archivo `requirements.txt`.

Para instalar todas las dependencias:

```
pip install -r requirements.txt
```