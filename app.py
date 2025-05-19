from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import os
import certifi
import ssl
from datetime import datetime
from flask import g
import hashlib
from functools import wraps
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuración para redirigir HTTP a HTTPS
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Importar configuración SSL
from ssl_config import certificados_ssl_existen, obtener_rutas_certificados, configurar_seguridad_produccion, crear_contexto_ssl

# Configurar seguridad en producción
if os.environ.get('FLASK_ENV') == 'production':
    app = configurar_seguridad_produccion(app)

# Context processor para proporcionar variables a todas las plantillas
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

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
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
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
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        email = request.form['email']
        password = hash_password(request.form['password'])
        rol = 'ahorrador'  # Por defecto, todos los usuarios nuevos son ahorradores
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s, %s, %s, %s, %s)",
                              (nombre, apellido, email, password, rol))
                conn.commit()
                flash('Registro exitoso. Por favor inicia sesión.', 'success')
                return redirect(url_for('login'))
            except mysql.connector.Error as err:
                flash(f'Error al registrar: {err}', 'danger')
            finally:
                cursor.close()
                conn.close()
    
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
                session['user_id'] = usuario['id']
                session['nombre'] = usuario['nombre']
                session['rol'] = usuario['rol']
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
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

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
                # Obtener la tasa de interés establecida por el administrador
                tasa_interes = float(request.form['tasa_interes'])
                cursor.execute("UPDATE prestamos SET estado = 'aprobado', tasa_interes = %s WHERE id = %s", 
                              (tasa_interes, prestamo_id))
                flash('Préstamo aprobado correctamente con tasa de interés del ' + str(tasa_interes) + '%', 'success')
            else:
                # Si no es POST, redirigir al panel de administración
                flash('Debe proporcionar una tasa de interés para aprobar el préstamo', 'warning')
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

@app.route('/ahorros', methods=['GET', 'POST'])
@login_required
def ahorros():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        monto = float(request.form['monto'])
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Los ahorros se registran con validado=0 por defecto, pendientes de validación por un administrador
            cursor.execute("INSERT INTO ahorros (usuario_id, monto, validado) VALUES (%s, %s, %s)", 
                          (session['user_id'], monto, 0))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Ahorro registrado correctamente. Pendiente de validación por un administrador.', 'success')
            return redirect(url_for('ahorros'))
    
    # Obtener historial de ahorros del usuario
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT *, CASE WHEN validado = 1 THEN 'Validado' ELSE 'Pendiente' END as estado FROM ahorros WHERE usuario_id = %s ORDER BY fecha DESC", (session['user_id'],))
        historial_ahorros = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return render_template('ahorros.html', historial_ahorros=historial_ahorros)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/prestamos', methods=['GET', 'POST'])
@login_required
def prestamos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        monto = float(request.form['monto'])
        plazo_meses = int(request.form['plazo_meses'])
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            # Los préstamos se registran con estado 'pendiente' por defecto, esperando aprobación de un administrador
            # La tasa de interés será establecida por el administrador al aprobar el préstamo
            cursor.execute("INSERT INTO prestamos (usuario_id, monto, plazo_meses, estado) VALUES (%s, %s, %s, %s)",
                          (session['user_id'], monto, plazo_meses, 'pendiente'))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Solicitud de préstamo enviada correctamente. Pendiente de aprobación por un administrador.', 'success')
            return redirect(url_for('prestamos'))
    
    # Obtener historial de préstamos del usuario
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM prestamos WHERE usuario_id = %s ORDER BY fecha_solicitud DESC", (session['user_id'],))
        historial_prestamos = cursor.fetchall()
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
        
        # Obtener ahorros
        cursor.execute("""
            SELECT id, monto, fecha, 'ahorro' as tipo, 'Depósito de ahorro' as descripcion 
            FROM ahorros 
            WHERE usuario_id = %s
        """, (user_id,))
        ahorros = cursor.fetchall()
        transacciones.extend(ahorros)
        
        # Obtener préstamos
        cursor.execute("""
            SELECT id, monto, fecha_solicitud as fecha, 'prestamo' as tipo, 
                   CONCAT('Préstamo a ', plazo_meses, ' meses') as descripcion 
            FROM prestamos 
            WHERE usuario_id = %s
        """, (user_id,))
        prestamos = cursor.fetchall()
        transacciones.extend(prestamos)
        
        # Obtener pagos de préstamos
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

@app.route('/calculadora')
@login_required
def calculadora():
    return render_template('calculadora.html')

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    user_id = session['user_id']
    conn = get_db_connection()
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
        usuario = cursor.fetchone()
        
        if request.method == 'POST':
            nombre = request.form['nombre']
            apellido = request.form['apellido']
            email = request.form['email']
            
            try:
                cursor.execute("UPDATE usuarios SET nombre = %s, apellido = %s, email = %s WHERE id = %s",
                              (nombre, apellido, email, user_id))
                conn.commit()
                session['nombre'] = nombre  # Actualizar el nombre en la sesión
                flash('Información actualizada correctamente', 'success')
                return redirect(url_for('perfil'))
            except mysql.connector.Error as err:
                flash(f'Error al actualizar: {err}', 'danger')
        
        # Obtener totales para el resumen
        cursor.execute("SELECT SUM(monto) as total_ahorros FROM ahorros WHERE usuario_id = %s", (user_id,))
        total_ahorros = cursor.fetchone()['total_ahorros'] or 0
        
        cursor.execute("SELECT COUNT(*) as num_prestamos FROM prestamos WHERE usuario_id = %s AND estado != 'pagado'", (user_id,))
        num_prestamos = cursor.fetchone()['num_prestamos'] or 0
        
        cursor.close()
        conn.close()
        
        return render_template('perfil.html', 
                              usuario=usuario, 
                              total_ahorros=total_ahorros,
                              num_prestamos=num_prestamos)
    
    flash('Error al conectar con la base de datos', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/cambiar_password', methods=['POST'])
@login_required
def cambiar_password():
    user_id = session['user_id']
    current_password = hash_password(request.form['current_password'])
    new_password = hash_password(request.form['new_password'])
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s AND password = %s", (user_id, current_password))
        usuario = cursor.fetchone()
        
        if usuario:
            cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (new_password, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Contraseña actualizada correctamente', 'success')
        else:
            cursor.close()
            conn.close()
            flash('La contraseña actual es incorrecta', 'danger')
    else:
        flash('Error al conectar con la base de datos', 'danger')
    
    return redirect(url_for('perfil'))

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