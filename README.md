# SparFonds - Sistema de Gestión de Ahorros y Préstamos

SparFonds es una aplicación web desarrollada con Flask que permite a los usuarios gestionar sus ahorros y solicitar préstamos en una plataforma segura y fácil de usar.

## Características

- **Gestión de usuarios**: Registro e inicio de sesión de usuarios con roles diferenciados (administrador y ahorrador).
- **Gestión de ahorros**: Los usuarios pueden registrar sus ahorros y ver su historial.
- **Solicitud de préstamos**: Los usuarios pueden solicitar préstamos que serán revisados por administradores.
- **Panel de administración**: Los administradores pueden validar ahorros y aprobar/rechazar solicitudes de préstamos.
- **Calculadora de préstamos**: Herramienta para calcular cuotas y total a pagar según monto, plazo e interés.

## Requisitos

- Python 3.6 o superior
- MySQL
- Paquetes de Python (ver `requirements.txt`)

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/sparfonds.git
   cd sparfonds
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurar la base de datos MySQL:
   - Crear una base de datos llamada `sparfonds`
   - Actualizar las credenciales de la base de datos en `app.py`

4. Iniciar la aplicación:
   ```
   python app.py
   ```

5. Acceder a la aplicación en el navegador:
   ```
   http://localhost:5000
   ```

## Estructura del Proyecto

```
sparfonds/
├── app.py                 # Aplicación principal de Flask
├── static/                # Archivos estáticos (CSS, JS)
│   ├── css/
│   └── js/
├── templates/             # Plantillas HTML
│   ├── admin.html         # Panel de administración
│   ├── ahorros.html       # Gestión de ahorros
│   ├── calculadora.html   # Calculadora de préstamos
│   ├── dashboard.html     # Panel principal del usuario
│   ├── layout.html        # Plantilla base
│   ├── login.html         # Inicio de sesión
│   ├── prestamos.html     # Gestión de préstamos
│   └── registro.html      # Registro de usuarios
└── actualizar_*.py        # Scripts de actualización
```

## Uso

1. **Registro de usuario**: Accede a la página de registro y completa el formulario.
2. **Inicio de sesión**: Utiliza tus credenciales para acceder al sistema.
3. **Gestión de ahorros**: Registra tus ahorros y visualiza tu historial.
4. **Solicitud de préstamos**: Completa el formulario con el monto y plazo deseado.
5. **Calculadora**: Utiliza la herramienta para simular diferentes escenarios de préstamos.

## Contribución

Si deseas contribuir a este proyecto, por favor:

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Realiza tus cambios y haz commit (`git commit -am 'Añadir nueva funcionalidad'`)
4. Sube los cambios a tu fork (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.