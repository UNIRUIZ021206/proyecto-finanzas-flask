from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from livereload import Server
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt # Para las contraseñas
import os # Para leer variables de entorno
from dotenv import load_dotenv # Para cargar el archivo .env

# Carga las variables del archivo .env en el entorno
load_dotenv()

# --- 1. Configuración Inicial ---
app = Flask(__name__)
# ¡MUY IMPORTANTE! Flask-Login necesita una 'secret_key' para firmar las cookies de sesión.
# Leemos la SECRET_KEY desde las variables de entorno para mayor seguridad.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'una-llave-por-defecto-si-no-hay-env')

# --- 2. Configuración de la Conexión a SQL Server ---
# Leemos los datos de conexión desde el archivo .env
SERVER_NAME = os.getenv('SERVER_NAME')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DRIVER_NAME = os.getenv('DRIVER_NAME')

# Construimos la cadena de conexión
connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{DATABASE_NAME}?driver={DRIVER_NAME}&trusted_connection=yes"
engine = create_engine(connection_string)

# --- 3. Configuración de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
# Si un usuario no logueado intenta entrar a una página protegida, lo redirige a '/login'
login_manager.login_view = 'login'
# Mensaje que se mostrará
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'error' # Categoría para el flash

# --- 4. Modelo de Usuario (para Flask-Login) ---
# Esta clase representa al usuario que sacamos de la BD
class User(UserMixin):
    def __init__(self, id, correo, id_rol):
        self.id = id
        self.correo = correo
        self.id_rol = id_rol

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login usa esto para recargar el objeto 'User' desde la sesión
    try:
        with engine.connect() as conn:
            query = text("SELECT Id_Usuario, Correo, Id_Rol FROM Usuarios WHERE Id_Usuario = :id AND Estado = 1")
            result = conn.execute(query, {"id": int(user_id)}).fetchone()
            if result:
                return User(id=result[0], correo=result[1], id_rol=result[2])
    except Exception as e:
        print(f"Error en user_loader: {e}")
        return None
    return None

# --- 5. Rutas de la Aplicación ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está logueado, lo mandamos al inicio
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena_form = request.form.get('contrasena')

        # Validaciones básicas
        if not correo or not contrasena_form:
            flash('Correo y contraseña son requeridos.', 'error')
            return render_template('login.html')

        try:
            with engine.connect() as conn:
                # 1. Buscar al usuario por correo Y que esté activo
                query = text("SELECT Id_Usuario, Correo, Contrasena, Id_Rol FROM Usuarios WHERE Correo = :correo AND Estado = 1")
                result = conn.execute(query, {"correo": correo}).fetchone()

                if result:
                    # 2. Verificar la contraseña
                    hash_bd_bytes = result[2] # El VARBINARY de la BD
                    contrasena_form_bytes = contrasena_form.encode('utf-8')

                    # ¡La comprobación con bcrypt!
                    if bcrypt.checkpw(contrasena_form_bytes, hash_bd_bytes):
                        # ¡Contraseña correcta! Creamos el objeto User y lo logueamos
                        usuario_obj = User(id=result[0], correo=result[1], id_rol=result[3])
                        login_user(usuario_obj) # <-- Aquí inicia la sesión
                        
                        return redirect(url_for('index'))
                    else:
                        flash('Correo o contraseña incorrecta.', 'error')
                else:
                    # No damos pistas si es el usuario o la contraseña por seguridad
                    flash('Correo o contraseña incorrecta.', 'error')
        
        except Exception as e:
            print(f"Error de conexión en login: {e}") # Imprime el error real en la terminal
            flash(f'Error al conectar con la base de datos.', 'error')

    # Si es GET (primera carga) o el login falló, mostramos la página de login
    return render_template('login.html')


@app.route('/logout')
@login_required # Solo un usuario logueado puede desloguearse
def logout():
    logout_user() # <-- Aquí cierra la sesión
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required # <-- ¡Ruta protegida!
def index():
    """Página de Bienvenida (Index)"""
    return render_template('index.html')


# --- Tus otras rutas, AHORA PROTEGIDAS ---

@app.route('/analisis-vertical/')
@login_required
def analisis_vertical():
    return "Página de Análisis Vertical - En construcción"

@app.route('/analisis-horizontal/')
@login_required
def analisis_horizontal():
    return "Página de Análisis Horizontal - En construcción"

@app.route('/ratios-financieros/')
@login_required
def ratios_financieros():
    return "Página de Ratios Financieros - En construcción"

@app.route('/origen-aplicacion/')
@login_required
def origen_aplicacion():
    return "Página de Origen y Aplicación - En construcción"


# --- 6. Ejecución con LiveReload ---
if __name__ == '__main__':
    server = Server(app.wsgi_app)
    server.watch('*.py')
    server.watch('templates/*.html') # Vigila TODOS los HTML
    server.watch('static/*.css')     # Vigila TODOS los CSS
    server.serve(port=5000, host='127.0.0.1', debug=True)