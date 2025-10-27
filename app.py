from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import os
import certifi
import ssl
from datetime import datetime
from flask import g
import hashlib
from functools import wraps
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configuración de secret key estable para sesiones
# Usar variable de entorno o generar una fija para desarrollo
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    # Para desarrollo, usar una clave fija
    SECRET_KEY = 'sparfonds-dev-key-2024-change-in-production'
    
app.secret_key = SECRET_KEY

# Configuración de sesiones para producción
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora
app.config['SESSION_COOKIE_NAME'] = 'sparfonds_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Función para detectar si estamos en producción
def is_production_environment():
    return (
        os.environ.get('FLASK_ENV') == 'production' or 
        os.environ.get('HTTPS') == 'on' or
        os.environ.get('FORCE_HTTPS') == 'true'
    )

is_production = is_production_environment()

# Configuración para HTTPS en producción
if is_production or os.environ.get('FORCE_HTTPS') == 'true':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
else:
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['PREFERRED_URL_SCHEME'] = 'http'

# Importar configuración SSL
from ssl_config import certificados_ssl_existen, obtener_rutas_certificados, configurar_seguridad_produccion, crear_contexto_ssl

# Configurar seguridad en producción
if is_production:
    app = configurar_seguridad_produccion(app)

# Context processor para proporcionar variables a todas las plantillas
@app.context_processor
def utility_processor():
    return dict(now=datetime.now)

# Configuración de la base de datos MySQL desde variables de entorno
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sparfonds')
}

# Función para conectar a la base de datos
def get_db_connection():
    try:
        # Usar certifi para proporcionar una ruta a certificados confiables
        ssl_ca = certifi.where()
        config = db_config.copy()
        config['ssl_ca'] = ssl_ca
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

# Crear tablas si no existen
def setup_database():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            cedula VARCHAR(20) UNIQUE NOT NULL,
            fecha_nacimiento DATE NOT NULL,
            direccion VARCHAR(255) NOT NULL,
            telefono VARCHAR(20) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            rol ENUM('admin', 'ahorrador') DEFAULT 'ahorrador',
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabla de ahorros
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ahorros (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT NOT NULL,
            monto DECIMAL(10, 2) NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            validado BOOLEAN DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        ''')
        
        # Tabla de préstamos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestamos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT NOT NULL,
            monto DECIMAL(10, 2) NOT NULL,
            tasa_interes DECIMAL(5, 2) NOT NULL,
            plazo_meses INT NOT NULL,
            fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado ENUM('pendiente', 'aprobado', 'rechazado', 'pagado') DEFAULT 'pendiente',
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        ''')
        
        # Tabla de pagos de préstamos
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos_prestamos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            prestamo_id INT NOT NULL,
            monto DECIMAL(10, 2) NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos configurada correctamente.")
    else:
        print("No se pudo configurar la base de datos.")

# Rutas de la aplicación
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Función para proteger rutas que requieren autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si la sesión existe y es válida
        if 'user_id' not in session:
            # Log para debugging
            print(f"Sesión no encontrada. Redirigiendo a login desde: {request.endpoint}")
            flash('Por favor inicia sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        
        # Renovar la sesión en cada request para mantenerla activa
        session.permanent = True
        
        return f(*args, **kwargs)
    return decorated_function

# Función para hashear contraseñas
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función para verificar si un usuario es administrador
def es_admin():
    if 'user_id' not in session:
        return False
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (session['user_id'],))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if usuario and usuario['rol'] == 'admin':
            return True
    return False

# Decorador para proteger rutas que requieren ser administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not es_admin():
            flash('Acceso denegado. Se requieren privilegios de administrador.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre')
            apellido = request.form.get('apellido')
            cedula = request.form.get('cedula')
            fecha_nacimiento = request.form.get('fecha_nacimiento')
            direccion = request.form.get('direccion')
            telefono = request.form.get('telefono')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Imprimir datos para depuración
            print(f"Datos recibidos: nombre={nombre}, apellido={apellido}, cedula={cedula}, "
                  f"fecha_nacimiento={fecha_nacimiento}, direccion={direccion}, telefono={telefono}, "
                  f"email={email}")

            # Validaciones
            if not all([nombre, apellido, cedula, fecha_nacimiento, direccion, telefono, email, password, confirm_password]):
                flash('Por favor complete todos los campos', 'error')
                return redirect(url_for('registro'))

            # Validar que cédula y teléfono contengan solo números
            if not cedula.isdigit():
                flash('La cédula debe contener solo números', 'error')
                return redirect(url_for('registro'))

            if not telefono.isdigit():
                flash('El teléfono debe contener solo números', 'error')
                return redirect(url_for('registro'))

            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return redirect(url_for('registro'))

            # Hash de la contraseña
            hashed_password = hash_password(password)

            # Conectar a la base de datos
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    
                    # Imprimir consulta SQL para depuración
                    sql = '''INSERT INTO usuarios 
                            (nombre, apellido, cedula, fecha_nacimiento, direccion, telefono, email, password) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
                    values = (nombre, apellido, cedula, fecha_nacimiento, direccion, telefono, email, hashed_password)
                    print(f"SQL: {sql}")
                    print(f"Valores: {values}")
                    
                    # Ejecutar la inserción
                    cursor.execute(sql, values)
                    conn.commit()
                    
                    print("Registro exitoso")
                    flash('Registro exitoso. Por favor inicie sesión.', 'success')
                    return redirect(url_for('login'))
                    
                except mysql.connector.Error as err:
                    print(f"Error MySQL: {err}")
                    if err.errno == 1062:  # Error de duplicado
                        if "cedula" in str(err):
                            flash('Esta cédula ya está registrada', 'error')
                        elif "email" in str(err):
                            flash('Este correo electrónico ya está registrado', 'error')
                        else:
                            flash('Error en el registro: datos duplicados', 'error')
                    else:
                        flash(f'Error en el registro: {err}', 'error')
                    return redirect(url_for('registro'))
                finally:
                    cursor.close()
                    conn.close()
            else:
                flash('Error de conexión a la base de datos', 'error')
                return redirect(url_for('registro'))
                
        except Exception as e:
            print(f"Error general: {e}")
            flash('Error en el registro', 'error')
            return redirect(url_for('registro'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hash_password(request.form['password'])
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s", (email, password))
            usuario = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if usuario:
                # Configurar sesión permanente para persistencia
                session.permanent = True
                session['user_id'] = usuario['id']
                session['nombre'] = usuario['nombre']
                session['rol'] = usuario['rol']
                
                # Log para debugging en producción
                print(f"Usuario {usuario['email']} logueado exitosamente. Session ID: {session.get('user_id')}")
                
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciales incorrectas', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener total de ahorros validados
        cursor.execute("SELECT SUM(monto) as total_ahorros FROM ahorros WHERE usuario_id = %s AND validado = 1", (user_id,))
        total_ahorros = cursor.fetchone()['total_ahorros'] or 0
        
        # Obtener total de ahorros pendientes de validación
        cursor.execute("SELECT SUM(monto) as total_pendiente FROM ahorros WHERE usuario_id = %s AND validado = 0", (user_id,))
        total_pendiente = cursor.fetchone()['total_pendiente'] or 0
        
        # Obtener préstamos activos
        cursor.execute("SELECT * FROM prestamos WHERE usuario_id = %s AND estado != 'pagado'", (user_id,))
        prestamos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', total_ahorros=total_ahorros, total_pendiente=total_pendiente, prestamos=prestamos)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
@admin_required
def admin():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener ahorros pendientes de validación
        cursor.execute("""
            SELECT a.*, u.nombre, u.apellido 
            FROM ahorros a 
            JOIN usuarios u ON a.usuario_id = u.id 
            WHERE a.validado = 0
        """)
        ahorros_pendientes = cursor.fetchall()
        
        # Obtener préstamos pendientes de aprobación
        cursor.execute("""
            SELECT p.*, u.nombre, u.apellido 
            FROM prestamos p 
            JOIN usuarios u ON p.usuario_id = u.id 
            WHERE p.estado = 'pendiente'
        """)
        prestamos_pendientes = cursor.fetchall()
        
        # Obtener todos los usuarios
        cursor.execute("SELECT * FROM usuarios ORDER BY fecha_registro DESC")
        usuarios = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin.html', 
                              ahorros_pendientes=ahorros_pendientes, 
                              prestamos_pendientes=prestamos_pendientes, 
                              usuarios=usuarios)

@app.route('/admin/ahorros', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_ahorros():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los usuarios ahorradores para el formulario
        cursor.execute("SELECT * FROM usuarios ORDER BY nombre ASC")
        usuarios = cursor.fetchall()
        
        if request.method == 'POST':
            usuario_id = int(request.form['usuario_id'])
            monto = float(request.form['monto'])
            fecha = request.form['fecha']
            validado = 1 if 'validado' in request.form else 0
            
            # Insertar el nuevo ahorro
            cursor.execute("INSERT INTO ahorros (usuario_id, monto, fecha, validado) VALUES (%s, %s, %s, %s)", 
                          (usuario_id, monto, fecha, validado))
            conn.commit()
            
            flash('Ahorro registrado correctamente para el ahorrador.', 'success')
            return redirect(url_for('admin_ahorros'))
        
        # Obtener los últimos ahorros registrados
        cursor.execute("""
            SELECT a.*, u.nombre, u.apellido 
            FROM ahorros a 
            JOIN usuarios u ON a.usuario_id = u.id 
            ORDER BY a.fecha DESC LIMIT 10
        """)
        ultimos_ahorros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin_ahorros.html', usuarios=usuarios, ultimos_ahorros=ultimos_ahorros)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('admin'))

@app.route('/validar_ahorro/<int:ahorro_id>/<accion>')
@login_required
@admin_required
def validar_ahorro(ahorro_id, accion):
    if accion not in ['aprobar', 'rechazar']:
        flash('Acción no válida', 'danger')
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        if accion == 'aprobar':
            cursor.execute("UPDATE ahorros SET validado = 1 WHERE id = %s", (ahorro_id,))
            flash('Ahorro validado correctamente', 'success')
        else:
            cursor.execute("DELETE FROM ahorros WHERE id = %s", (ahorro_id,))
            flash('Ahorro rechazado correctamente', 'success')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin'))

@app.route('/validar_prestamo/<int:prestamo_id>/<accion>', methods=['GET', 'POST'])
@login_required
@admin_required
def validar_prestamo(prestamo_id, accion):
    if accion not in ['aprobar', 'rechazar']:
        flash('Acción no válida', 'danger')
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        if accion == 'aprobar':
            if request.method == 'POST':
                # Obtener la tasa de interés y plazo establecidos por el administrador
                tasa_interes = float(request.form['tasa_interes'])
                plazo_meses = int(request.form['plazo_meses'])
                
                # Obtener el monto del préstamo para calcular interés simple anualizado
                cursor.execute("SELECT monto FROM prestamos WHERE id = %s", (prestamo_id,))
                monto_prestamo = cursor.fetchone()[0]
                
                # Calcular interés mensual fijo: (monto * tasa_anual) / 12 meses
                interes_anual = float(monto_prestamo) * (tasa_interes / 100)
                interes_mensual_fijo = interes_anual / 12
                
                # Calcular cuota de capital mensual: monto / plazo
                cuota_capital_mensual = float(monto_prestamo) / plazo_meses
                
                # Actualizar préstamo con nuevo sistema de interés simple
                cursor.execute("""
                    UPDATE prestamos 
                    SET estado = 'aprobado', 
                        tasa_interes = %s, 
                        plazo_meses = %s,
                        interes_mensual_fijo = %s,
                        cuota_capital_mensual = %s
                    WHERE id = %s
                """, (tasa_interes, plazo_meses, interes_mensual_fijo, cuota_capital_mensual, prestamo_id))
                
                flash(f'Préstamo aprobado con interés simple anualizado: {tasa_interes}% anual = ${interes_mensual_fijo:.2f} mensual fijo + ${cuota_capital_mensual:.2f} capital por {plazo_meses} meses', 'success')
            else:
                # Si no es POST, redirigir al panel de administración
                flash('Debe proporcionar una tasa de interés y plazo para aprobar el préstamo', 'warning')
                return redirect(url_for('admin'))
        else:
            cursor.execute("UPDATE prestamos SET estado = 'rechazado' WHERE id = %s", (prestamo_id,))
            flash('Préstamo rechazado correctamente', 'success')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin'))

@app.route('/cambiar_rol/<int:usuario_id>')
@login_required
@admin_required
def cambiar_rol(usuario_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener rol actual
        cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        
        if usuario:
            nuevo_rol = 'ahorrador' if usuario['rol'] == 'admin' else 'admin'
            cursor.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, usuario_id))
            conn.commit()
            flash(f'Rol de usuario actualizado a {nuevo_rol}', 'success')
        
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin'))

@app.route('/ahorros', methods=['GET'])
@login_required
def ahorros():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Obtener historial de ahorros del usuario
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener historial de ahorros
        cursor.execute("SELECT *, CASE WHEN validado = 1 THEN 'Validado' ELSE 'Pendiente' END as estado FROM ahorros WHERE usuario_id = %s ORDER BY fecha DESC", (user_id,))
        historial_ahorros = cursor.fetchall()
        
        # Calcular total de ahorros validados
        cursor.execute("SELECT SUM(monto) as total_ahorros FROM ahorros WHERE usuario_id = %s AND validado = 1", (user_id,))
        total_ahorros = cursor.fetchone()['total_ahorros'] or 0
        
        cursor.close()
        conn.close()
        
        return render_template('ahorros.html', historial_ahorros=historial_ahorros, total_ahorros=total_ahorros)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/prestamos', methods=['GET', 'POST'])
@login_required
def prestamos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        monto = float(request.form['monto'])
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Los préstamos se registran con estado 'pendiente' por defecto, esperando aprobación de un administrador
            # La tasa de interés y el plazo serán establecidos por el administrador al aprobar el préstamo
            # Incluimos valores por defecto temporales para tasa_interes y plazo_meses
            cursor.execute("INSERT INTO prestamos (usuario_id, monto, estado, tasa_interes, plazo_meses) VALUES (%s, %s, %s, %s, %s)",
                          (session['user_id'], monto, 'pendiente', 0.0, 0))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Solicitud de préstamo enviada correctamente. Pendiente de aprobación por un administrador.', 'success')
            return redirect(url_for('prestamos'))
    
    # Obtener historial de préstamos del usuario con saldo pendiente y pagos
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM prestamos WHERE usuario_id = %s ORDER BY fecha_solicitud DESC", (session['user_id'],))
        historial_prestamos = cursor.fetchall()
        
        # Para cada préstamo aprobado, calcular el saldo pendiente y obtener historial de pagos
        for prestamo in historial_prestamos:
            if prestamo['estado'] == 'aprobado':
                # Obtener la suma de pagos realizados para este préstamo
                cursor.execute("SELECT SUM(monto) as total_pagado FROM pagos_prestamos WHERE prestamo_id = %s", (prestamo['id'],))
                resultado = cursor.fetchone()
                total_pagado = resultado['total_pagado'] if resultado['total_pagado'] else 0
                
                # Calcular saldo pendiente
                prestamo['saldo_pendiente'] = round(float(prestamo['monto']) - float(total_pagado), 2)
                
                # Calcular información de cuotas con interés simple (acceso defensivo)
                interes_mensual_fijo = prestamo.get('interes_mensual_fijo')
                cuota_capital_mensual = prestamo.get('cuota_capital_mensual')
                plazo_meses = prestamo.get('plazo_meses', 0)
                if interes_mensual_fijo is not None and cuota_capital_mensual is not None and plazo_meses:
                    prestamo['cuota_total_mensual'] = float(interes_mensual_fijo) + float(cuota_capital_mensual)
                    prestamo['total_intereses'] = float(interes_mensual_fijo) * int(plazo_meses)
                    prestamo['total_a_pagar'] = float(prestamo['monto']) + prestamo['total_intereses']
                else:
                    # Para préstamos antiguos sin el nuevo sistema o sin columnas
                    prestamo['cuota_total_mensual'] = None
                    prestamo['total_intereses'] = None
                    prestamo['total_a_pagar'] = None
                
                # Obtener historial de pagos
                cursor.execute("SELECT * FROM pagos_prestamos WHERE prestamo_id = %s ORDER BY fecha DESC", (prestamo['id'],))
                prestamo['pagos'] = cursor.fetchall()
            else:
                prestamo['saldo_pendiente'] = prestamo['monto']
                prestamo['pagos'] = []
                prestamo['cuota_total_mensual'] = None
                prestamo['total_intereses'] = None
                prestamo['total_a_pagar'] = None
        
        cursor.close()
        conn.close()
        
        return render_template('prestamos.html', historial_prestamos=historial_prestamos)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/historial')
@login_required
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    transacciones = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener ahorros - Solo los del usuario logueado
        cursor.execute("""
            SELECT id, monto, fecha, 'ahorro' as tipo, 'Depósito de ahorro' as descripcion 
            FROM ahorros 
            WHERE usuario_id = %s
        """, (user_id,))
        ahorros = cursor.fetchall()
        transacciones.extend(ahorros)
        
        # Obtener préstamos - Solo los del usuario logueado
        cursor.execute("""
            SELECT id, monto, fecha_solicitud as fecha, 'prestamo' as tipo, 
                   CONCAT('Préstamo a ', plazo_meses, ' meses') as descripcion 
            FROM prestamos 
            WHERE usuario_id = %s
        """, (user_id,))
        prestamos = cursor.fetchall()
        transacciones.extend(prestamos)
        
        # Obtener pagos de préstamos - Solo los del usuario logueado
        cursor.execute("""
            SELECT pp.id, pp.monto, pp.fecha, 'pago' as tipo, 
                   'Pago de préstamo' as descripcion 
            FROM pagos_prestamos pp
            JOIN prestamos p ON pp.prestamo_id = p.id
            WHERE p.usuario_id = %s
        """, (user_id,))
        pagos = cursor.fetchall()
        transacciones.extend(pagos)
        
        # Ordenar por fecha (más reciente primero)
        transacciones.sort(key=lambda x: x['fecha'], reverse=True)
        
        # Obtener totales
        cursor.execute("SELECT SUM(monto) as total_ahorros FROM ahorros WHERE usuario_id = %s", (user_id,))
        total_ahorros = cursor.fetchone()['total_ahorros'] or 0
        
        cursor.execute("""
            SELECT SUM(monto) as total_prestamos 
            FROM prestamos 
            WHERE usuario_id = %s AND estado != 'pagado'
        """, (user_id,))
        total_prestamos = cursor.fetchone()['total_prestamos'] or 0
        
        cursor.close()
        conn.close()
        
        return render_template('historial.html', 
                              transacciones=transacciones, 
                              total_ahorros=total_ahorros,
                              total_prestamos=total_prestamos)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/admin/historial')
@login_required
@admin_required
def admin_historial():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los usuarios ahorradores para el selector
        cursor.execute("SELECT * FROM usuarios ORDER BY nombre ASC")
        usuarios = cursor.fetchall()
        
        # Verificar si se ha seleccionado un usuario
        usuario_id = request.args.get('usuario_id')
        usuario_seleccionado = None
        transacciones = []
        total_ahorros = 0
        total_prestamos = 0
        
        if usuario_id:
            # Obtener información del usuario seleccionado
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
            usuario_seleccionado = cursor.fetchone()
            
            if usuario_seleccionado:
                # Obtener ahorros del usuario seleccionado
                cursor.execute("""
                    SELECT id, monto, fecha, 'ahorro' as tipo, 'Depósito de ahorro' as descripcion 
                    FROM ahorros 
                    WHERE usuario_id = %s
                """, (usuario_id,))
                ahorros = cursor.fetchall()
                transacciones.extend(ahorros)
                
                # Obtener préstamos del usuario seleccionado
                cursor.execute("""
                    SELECT id, monto, fecha_solicitud as fecha, 'prestamo' as tipo, 
                           CONCAT('Préstamo a ', plazo_meses, ' meses') as descripcion 
                    FROM prestamos 
                    WHERE usuario_id = %s
                """, (usuario_id,))
                prestamos = cursor.fetchall()
                transacciones.extend(prestamos)
                
                # Obtener pagos de préstamos del usuario seleccionado
                cursor.execute("""
                    SELECT pp.id, pp.monto, pp.fecha, 'pago' as tipo, 
                           'Pago de préstamo' as descripcion 
                    FROM pagos_prestamos pp
                    JOIN prestamos p ON pp.prestamo_id = p.id
                    WHERE p.usuario_id = %s
                """, (usuario_id,))
                pagos = cursor.fetchall()
                transacciones.extend(pagos)
                
                # Ordenar por fecha (más reciente primero)
                transacciones.sort(key=lambda x: x['fecha'], reverse=True)
                
                # Obtener totales
                cursor.execute("SELECT SUM(monto) as total_ahorros FROM ahorros WHERE usuario_id = %s", (usuario_id,))
                total_ahorros = cursor.fetchone()['total_ahorros'] or 0
                
                cursor.execute("""
                    SELECT SUM(monto) as total_prestamos 
                    FROM prestamos 
                    WHERE usuario_id = %s AND estado != 'pagado'
                """, (usuario_id,))
                total_prestamos = cursor.fetchone()['total_prestamos'] or 0
        
        cursor.close()
        conn.close()
        
        return render_template('admin_historial.html', 
                              usuarios=usuarios,
                              usuario_seleccionado=usuario_seleccionado,
                              transacciones=transacciones, 
                              total_ahorros=total_ahorros,
                              total_prestamos=total_prestamos)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('admin'))

@app.route('/calculadora')
@login_required
def calculadora():
    return render_template('calculadora.html')

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            fecha_nacimiento = request.form['fecha_nacimiento']
            direccion = request.form['direccion']
            telefono = request.form['telefono']
            email = request.form['email']
            
            # Validar que todos los campos requeridos estén presentes
            if not all([nombre, apellido, fecha_nacimiento, direccion, telefono, email]):
                flash('Por favor complete todos los campos requeridos', 'danger')
                return redirect(url_for('perfil'))
            
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        UPDATE usuarios 
                        SET nombre = %s, apellido = %s, fecha_nacimiento = %s, 
                            direccion = %s, telefono = %s, email = %s 
                        WHERE id = %s
                    """, (nombre, apellido, fecha_nacimiento, 
                         direccion, telefono, email, user_id))
                    conn.commit()
                    flash('Perfil actualizado exitosamente', 'success')
                except mysql.connector.Error as err:
                    if err.errno == 1062:  # Error de duplicado
                        if "email" in str(err):
                            flash('El correo electrónico ya está registrado', 'danger')
                        else:
                            flash('Error: Valor duplicado', 'danger')
                    else:
                        flash(f'Error al actualizar perfil: {err}', 'danger')
                finally:
                    cursor.close()
                    conn.close()
                return redirect(url_for('perfil'))
        except Exception as e:
            flash(f'Error al procesar el formulario: {str(e)}', 'danger')
            return redirect(url_for('perfil'))
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Obtener información del usuario
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
        usuario = cursor.fetchone()
        
        # Obtener total de ahorros validados
        cursor.execute("SELECT SUM(monto) as total_ahorros FROM ahorros WHERE usuario_id = %s AND validado = 1", (user_id,))
        total_ahorros = cursor.fetchone()['total_ahorros'] or 0
        
        # Obtener total de préstamos activos
        cursor.execute("""
            SELECT COUNT(*) as num_prestamos, COALESCE(SUM(monto), 0) as total_prestamos 
            FROM prestamos 
            WHERE usuario_id = %s AND estado != 'pagado'
        """, (user_id,))
        prestamos_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('perfil.html', 
                             usuario=usuario,
                             total_ahorros=total_ahorros,
                             num_prestamos=prestamos_info['num_prestamos'],
                             total_prestamos=prestamos_info['total_prestamos'])
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/cambiar_password', methods=['POST'])
@login_required
def cambiar_password():
    user_id = session['user_id']
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    # Verificar que las contraseñas nuevas coinciden
    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden', 'danger')
        return redirect(url_for('perfil'))
    
    # Verificar la contraseña actual
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password FROM usuarios WHERE id = %s", (user_id,))
        usuario = cursor.fetchone()
        
        if not usuario or usuario['password'] != hash_password(current_password):
            cursor.close()
            conn.close()
            flash('La contraseña actual es incorrecta', 'danger')
            return redirect(url_for('perfil'))
        
        # Actualizar la contraseña
        try:
            cursor.execute("""
                UPDATE usuarios 
                SET password = %s 
                WHERE id = %s
            """, (hash_password(new_password), user_id))
            conn.commit()
            flash('Contraseña actualizada exitosamente', 'success')
        except mysql.connector.Error as err:
            flash(f'Error al actualizar la contraseña: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Error al conectar con la base de datos', 'danger')
    
    return redirect(url_for('perfil'))

# FUNCIONES PARA CÁLCULO DE TABLA DE AMORTIZACIÓN
def calcular_tabla_amortizacion(monto_prestamo, tasa_interes_anual, plazo_meses):
    """
    Calcula la tabla de amortización para un préstamo
    Retorna lista de diccionarios con mes, abono_capital, interes, cuota_total, saldo_restante
    """
    if not all([monto_prestamo, tasa_interes_anual, plazo_meses]) or plazo_meses <= 0:
        return []
    
    try:
        # Convertir tasa anual a mensual
        tasa_interes_mensual = float(tasa_interes_anual) / 100 / 12
        monto = float(monto_prestamo)
        plazo = int(plazo_meses)
        
        # Calcular cuota fija mensual (método francés)
        if tasa_interes_mensual > 0:
            cuota_fija = monto * (tasa_interes_mensual * (1 + tasa_interes_mensual)**plazo) / ((1 + tasa_interes_mensual)**plazo - 1)
        else:
            cuota_fija = monto / plazo
        
        tabla = []
        saldo_restante = monto
        
        for mes in range(1, plazo + 1):
            # Calcular interés del mes
            interes_mes = saldo_restante * tasa_interes_mensual
            
            # Calcular abono a capital
            abono_capital = cuota_fija - interes_mes
            
            # Actualizar saldo
            saldo_restante -= abono_capital
            
            # Ajustar última cuota para evitar decimales
            if mes == plazo:
                abono_capital += saldo_restante
                saldo_restante = 0
            
            tabla.append({
                'mes': mes,
                'abono_capital': round(abono_capital, 2),
                'interes': round(interes_mes, 2),
                'cuota_total': round(cuota_fija, 2),
                'saldo_restante': round(saldo_restante, 2)
            })
        
        return tabla
    except Exception as e:
        print(f"Error calculando tabla de amortización: {e}")
        return []

# ENDPOINTS API PARA ADMINISTRADOR - DETALLES DE AHORROS
@app.route('/api/admin/ahorro/<int:ahorro_id>')
@login_required
@admin_required
def api_detalle_ahorro(ahorro_id):
    """Obtiene detalles completos de un ahorro específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener información del ahorro con datos del usuario
        cursor.execute("""
            SELECT a.*, u.nombre, u.apellido, u.email, u.fecha_registro as fecha_usuario
            FROM ahorros a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.id = %s
        """, (ahorro_id,))
        
        ahorro = cursor.fetchone()
        
        if not ahorro:
            return jsonify({'error': 'Ahorro no encontrado'}), 404
        
        # Obtener total de ahorros del usuario
        cursor.execute("""
            SELECT SUM(monto) as total_ahorros, COUNT(*) as cantidad_ahorros
            FROM ahorros
            WHERE usuario_id = %s
        """, (ahorro['usuario_id'],))
        
        resumen = cursor.fetchone()
        
        # Obtener historial de validaciones (si existe tabla de auditoría)
        # Por ahora, solo mostramos el estado actual
        
        response = {
            'id': ahorro['id'],
            'monto': float(ahorro['monto']),
            'fecha': ahorro['fecha'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(ahorro['fecha'], datetime) else str(ahorro['fecha']),
            'validado': bool(ahorro['validado']),
            'usuario': {
                'id': ahorro['usuario_id'],
                'nombre': ahorro['nombre'],
                'apellido': ahorro['apellido'],
                'email': ahorro['email'],
                'fecha_registro': ahorro['fecha_usuario'].strftime('%Y-%m-%d') if isinstance(ahorro['fecha_usuario'], datetime) else str(ahorro['fecha_usuario'])
            },
            'resumen_usuario': {
                'total_ahorros': float(resumen['total_ahorros'] or 0),
                'cantidad_ahorros': resumen['cantidad_ahorros']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error obteniendo detalles de ahorro: {e}")
        return jsonify({'error': 'Error al obtener detalles del ahorro'}), 500
    
    finally:
        cursor.close()
        conn.close()

# ENDPOINTS API PARA ADMINISTRADOR - PRÓSTICO DE PRÉSTAMOS
@app.route('/api/admin/prestamo/<int:prestamo_id>/pronostico')
@login_required
@admin_required
def api_pronostico_prestamo(prestamo_id):
    """Obtiene el pronóstico de pagos de un préstamo específico"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener información del préstamo con datos del usuario
        cursor.execute("""
            SELECT p.*, u.nombre, u.apellido, u.email,
                   COALESCE(p.interes_mensual_fijo, 0) as interes_mensual_fijo,
                   COALESCE(p.cuota_capital_mensual, 0) as cuota_capital_mensual
            FROM prestamos p
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = %s
        """, (prestamo_id,))
        
        prestamo = cursor.fetchone()
        
        if not prestamo:
            return jsonify({'error': 'Préstamo no encontrado'}), 404
        
        # Calcular tabla de amortización
        tabla_amortizacion = calcular_tabla_amortizacion(
            prestamo['monto'],
            prestamo['tasa_interes'],
            prestamo['plazo_meses']
        )
        
        # Obtener pagos realizados
        cursor.execute("""
            SELECT COUNT(*) as pagos_realizados, SUM(monto) as total_pagado
            FROM pagos_prestamos
            WHERE prestamo_id = %s
        """, (prestamo_id,))
        
        pagos_info = cursor.fetchone()
        
        # Formatear tabla de amortización al formato esperado por el template
        cuota_mensual = tabla_amortizacion[0]['cuota_total'] if tabla_amortizacion else 0.0
        tabla_amortizacion_formateada = [
            {
                'mes': item['mes'],
                'cuota_total': item['cuota_total'],
                'capital': item['abono_capital'],
                'interes': item['interes'],
                'saldo_pendiente': item['saldo_restante']
            } for item in tabla_amortizacion
        ]

        total_pagado = float(pagos_info['total_pagado'] or 0)
        total_intereses = float(sum(item['interes'] for item in tabla_amortizacion))
        saldo_pendiente = float(prestamo['monto']) - total_pagado

        # Calcular fecha de finalización (fecha_solicitud + plazo_meses)
        try:
            fecha_solicitud_dt = prestamo['fecha_solicitud'] if isinstance(prestamo['fecha_solicitud'], datetime) else datetime.strptime(str(prestamo['fecha_solicitud']), '%Y-%m-%d %H:%M:%S') if ' ' in str(prestamo['fecha_solicitud']) else datetime.strptime(str(prestamo['fecha_solicitud']), '%Y-%m-%d')
        except Exception:
            fecha_solicitud_dt = datetime.now()
        import calendar
        year = fecha_solicitud_dt.year
        month = fecha_solicitud_dt.month + int(prestamo['plazo_meses'])
        day = fecha_solicitud_dt.day
        year += (month - 1) // 12
        month = ((month - 1) % 12) + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        fecha_finalizacion_dt = datetime(year, month, day)
        
        response = {
            'monto_prestamo': float(prestamo['monto']),
            'tasa_interes': float(prestamo['tasa_interes']),
            'plazo_meses': int(prestamo['plazo_meses']),
            'cuota_mensual': float(cuota_mensual),
            'tabla_amortizacion': tabla_amortizacion_formateada,
            'total_pagado': total_pagado,
            'total_intereses': total_intereses,
            'fecha_finalizacion': fecha_finalizacion_dt.strftime('%Y-%m-%d')
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error obteniendo pronóstico de préstamo: {e}")
        return jsonify({'error': 'Error al obtener pronóstico del préstamo'}), 500
    
    finally:
        cursor.close()
        conn.close()

# ACTUALIZAR ESTADO DE AHORRO (VALIDAR/INVALIDAR)
@app.route('/api/admin/ahorro/<int:ahorro_id>/validar', methods=['POST'])
@login_required
@admin_required
def api_validar_ahorro(ahorro_id):
    """Actualiza el estado de validación de un ahorro"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    cursor = conn.cursor()
    
    try:
        data = request.get_json()
        validado = data.get('validado', False)
        
        cursor.execute("""
            UPDATE ahorros 
            SET validado = %s 
            WHERE id = %s
        """, (validado, ahorro_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Ahorro no encontrado'}), 404
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Ahorro {"validado" if validado else "invalidado"} exitosamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Error actualizando ahorro: {e}")
        return jsonify({'error': 'Error al actualizar el ahorro'}), 500
    
    finally:
        cursor.close()
        conn.close()

# ACTUALIZAR ESTADO DE PRÉSTAMO
@app.route('/api/admin/prestamo/<int:prestamo_id>/estado', methods=['POST'])
@login_required
@admin_required
def api_actualizar_estado_prestamo(prestamo_id):
    """Actualiza el estado de un préstamo"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
    
    cursor = conn.cursor()
    
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        if nuevo_estado not in ['pendiente', 'aprobado', 'rechazado', 'pagado']:
            return jsonify({'error': 'Estado inválido'}), 400
        
        cursor.execute("""
            UPDATE prestamos 
            SET estado = %s 
            WHERE id = %s
        """, (nuevo_estado, prestamo_id))
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Préstamo no encontrado'}), 404
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'mensaje': f'Préstamo marcado como {nuevo_estado} exitosamente'
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Error actualizando préstamo: {e}")
        return jsonify({'error': 'Error al actualizar el préstamo'}), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/pagos_prestamos', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_pagos_prestamos():
    conn = get_db_connection()
    if not conn:
        flash('Error al conectar con la base de datos', 'danger')
        return redirect(url_for('admin'))

    cursor = conn.cursor(dictionary=True)
    try:
        # Cargar lista de usuarios para el selector
        cursor.execute("SELECT * FROM usuarios ORDER BY nombre ASC")
        usuarios = cursor.fetchall()

        if request.method == 'POST':
            usuario_id = int(request.form['usuario_id'])
            prestamo_id = int(request.form['prestamo_id'])
            monto = float(request.form['monto'])
            fecha = request.form.get('fecha')  # opcional, por defecto NOW()

            # Validar que el préstamo pertenece al usuario y está aprobado
            cursor.execute("SELECT * FROM prestamos WHERE id = %s AND usuario_id = %s", (prestamo_id, usuario_id))
            prestamo = cursor.fetchone()
            if not prestamo:
                flash('Préstamo no encontrado para el ahorrador seleccionado', 'danger')
                return redirect(url_for('admin_pagos_prestamos'))

            # Calcular saldo pendiente con pagos previos
            cursor.execute("SELECT COALESCE(SUM(monto), 0) as total_pagado FROM pagos_prestamos WHERE prestamo_id = %s", (prestamo_id,))
            total_pagado = cursor.fetchone()['total_pagado'] or 0
            saldo_pendiente = float(prestamo['monto']) - float(total_pagado)

            # No permitir pagar más del saldo
            if monto > saldo_pendiente:
                flash('El monto del pago excede el saldo pendiente', 'warning')
                return redirect(url_for('admin_pagos_prestamos'))

            # Registrar el pago
            if fecha:
                cursor.execute(
                    "INSERT INTO pagos_prestamos (prestamo_id, monto, fecha) VALUES (%s, %s, %s)",
                    (prestamo_id, monto, fecha)
                )
            else:
                cursor.execute(
                    "INSERT INTO pagos_prestamos (prestamo_id, monto) VALUES (%s, %s)",
                    (prestamo_id, monto)
                )
            conn.commit()

            # Recalcular saldo y actualizar estado si se pagó completo
            nuevo_total_pagado = total_pagado + monto
            nuevo_saldo = float(prestamo['monto']) - float(nuevo_total_pagado)
            if nuevo_saldo <= 0:
                cursor.execute("UPDATE prestamos SET estado = 'pagado' WHERE id = %s", (prestamo_id,))
                conn.commit()

            flash('Pago registrado correctamente', 'success')
            return redirect(url_for('admin_pagos_prestamos'))

        # Obtener últimos pagos registrados con datos del usuario
        cursor.execute(
            """
            SELECT pp.*, u.nombre, u.apellido,
                   (p.monto - COALESCE(SUM(pp2.monto), 0)) AS saldo_restante
            FROM pagos_prestamos pp
            JOIN prestamos p ON pp.prestamo_id = p.id
            JOIN usuarios u ON p.usuario_id = u.id
            LEFT JOIN pagos_prestamos pp2 ON pp2.prestamo_id = p.id AND pp2.fecha <= pp.fecha
            GROUP BY pp.id
            ORDER BY pp.fecha DESC
            LIMIT 10
            """
        )
        ultimos_pagos = cursor.fetchall()

        return render_template('admin_pagos_prestamos.html', usuarios=usuarios, ultimos_pagos=ultimos_pagos)
    except Exception as e:
        print(f"Error en admin_pagos_prestamos: {e}")
        flash('Error al cargar la página de pagos de préstamos', 'danger')
        return redirect(url_for('admin'))
    finally:
        cursor.close()
        conn.close()

# (eliminado bloque duplicado de arranque)

# Función para crear un usuario administrador inicial si no existe
def crear_admin_inicial():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si la columna 'rol' existe en la tabla usuarios
        try:
            # Intentar verificar si ya existe un administrador
            cursor.execute("SELECT * FROM usuarios WHERE rol = 'admin' LIMIT 1")
            admin_existente = cursor.fetchone()
            
            if not admin_existente:
                # Crear un administrador por defecto
                nombre = 'Admin'
                apellido = 'Sistema'
                email = 'admin@sparfonds.com'
                password = hash_password('admin123')
                rol = 'admin'
                
                cursor.execute("INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s, %s, %s, %s, %s)",
                              (nombre, apellido, email, password, rol))
                conn.commit()
                print("Usuario administrador creado con éxito.")
                print("Email: admin@sparfonds.com")
                print("Contraseña: admin123")
        except mysql.connector.Error as err:
            # Si hay un error porque la columna 'rol' no existe
            if "Unknown column 'rol'" in str(err):
                print("La columna 'rol' no existe en la tabla usuarios. Añadiendo la columna...")
                # Añadir la columna 'rol' a la tabla usuarios
                cursor.execute("ALTER TABLE usuarios ADD COLUMN rol ENUM('admin', 'ahorrador') DEFAULT 'ahorrador'")
                conn.commit()
                print("Columna 'rol' añadida correctamente. Intentando crear administrador...")
                
                # Intentar crear el administrador nuevamente
                cursor.execute("SELECT * FROM usuarios WHERE email = 'admin@sparfonds.com' LIMIT 1")
                admin_existente = cursor.fetchone()
                
                if not admin_existente:
                    # Crear un administrador por defecto
                    nombre = 'Admin'
                    apellido = 'Sistema'
                    email = 'admin@sparfonds.com'
                    password = hash_password('admin123')
                    rol = 'admin'
                    
                    cursor.execute("INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s, %s, %s, %s, %s)",
                                  (nombre, apellido, email, password, rol))
                    conn.commit()
                    print("Usuario administrador creado con éxito.")
                    print("Email: admin@sparfonds.com")
                    print("Contraseña: admin123")
                else:
                    # Actualizar el rol del administrador existente
                    cursor.execute("UPDATE usuarios SET rol = 'admin' WHERE email = 'admin@sparfonds.com'")
                    conn.commit()
                    print("Rol de administrador actualizado para el usuario existente.")
            else:
                # Si es otro tipo de error, mostrarlo
                print(f"Error al verificar/crear administrador: {err}")
        
        cursor.close()
        conn.close()

# Iniciar la aplicación
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

# Ruta para redirigir HTTP a HTTPS
@app.before_request
def redirigir_a_https():
    # Solo redirigir en producción y cuando no sea una solicitud HTTPS
    if os.environ.get('FLASK_ENV') == 'production' and not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

if __name__ == '__main__':
    setup_database()
    crear_admin_inicial()
    
    # Verificar si existen certificados SSL
    ssl_context = crear_contexto_ssl()
    if ssl_context:
        # Ejecutar con SSL
        print("Iniciando servidor con SSL en https://localhost:8081")
        app.run(debug=True, ssl_context=ssl_context, host='0.0.0.0', port=8081)
    else:
        print("ADVERTENCIA: Ejecutando sin SSL. Genere certificados con 'python generar_certificados.py'")
        print("El servidor estará disponible en http://localhost:8081")
        app.run(debug=True, host='0.0.0.0', port=8081)