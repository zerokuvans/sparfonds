"""
WSGI entry point para servidores como Gunicorn/uWSGI/Waitress.
Carga la app Flask desde app.py y prepara entorno de producción.
"""

import os
import logging

from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Asegurar entorno de producción por defecto bajo WSGI (puede ser sobrescrito externamente)
os.environ.setdefault("FLASK_ENV", "production")

try:
    # Importar la aplicación Flask creada en app.py
    from app import app as application
except Exception as e:
    # Registrar el error y exponer una app mínima para no devolver 502 vacíos
    logging.exception("Error al importar la aplicación Flask desde app.py: %s", e)
    from flask import Flask

    application = Flask(__name__)

    @application.route("/")
    def _wsgi_error():
        return (
            "WSGI no pudo cargar la aplicación principal. Revisa los logs del servidor.",
            500,
        )