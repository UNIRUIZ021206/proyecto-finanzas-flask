# app/auth/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
import bcrypt
from sqlalchemy import text

# Importamos engine, User y funciones de utils
from ..extensions import engine
from ..models import User
from ..utils import get_rol_name_by_id, get_rol_id_by_name

# 1. Creamos el Blueprint
# No especificamos template_folder para usar el de la app principal
auth_bp = Blueprint('auth', __name__)

# 2. Cambiamos @app.route por @auth_bp.route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # ¡IMPORTANTE! Actualizar a la ruta del blueprint
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena_form = request.form.get('contrasena')

        if not correo or not contrasena_form:
            flash('Correo y contraseña son requeridos.', 'error')
            return render_template('login.html')

        try:
            with engine.connect() as conn:
                query = text("SELECT Id_Usuario, Nombre, Correo, Contrasena, Id_Rol FROM Usuarios WHERE Correo = :correo AND Estado = 1")
                result = conn.execute(query, {"correo": correo}).fetchone()

                if result:
                    hash_bd_bytes = result[3]
                    contrasena_form_bytes = contrasena_form.encode('utf-8')

                    if bcrypt.checkpw(contrasena_form_bytes, hash_bd_bytes):
                        usuario_obj = User(id=result[0], nombre=result[1], correo=result[2], id_rol=result[4])
                        login_user(usuario_obj)
                        rol_nombre = get_rol_name_by_id(result[4])
                        
                        # ¡IMPORTANTE! Actualizar a la ruta del blueprint
                        if rol_nombre and rol_nombre.lower() == 'cliente':
                            return redirect(url_for('main.dashboard_cliente'))
                        return redirect(url_for('main.index'))
                    else:
                        flash('Correo o contraseña incorrecta.', 'error')
                else:
                    flash('Correo o contraseña incorrecta.', 'error')

        except Exception as e:
            print(f"Error de conexión en login: {e}")
            flash(f'Error al conectar con la base de datos.', 'error')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        # ¡IMPORTANTE! Actualizar a la ruta del blueprint
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        correo = request.form.get('correo', '').strip().lower()
        contrasena = request.form.get('contrasena', '')
        contrasena_confirm = request.form.get('contrasena_confirm', '')

        # Validaciones básicas
        if not nombre:
            flash('El nombre es requerido.', 'error')
            return render_template('register.html')
        
        if not correo:
            flash('El correo electrónico es requerido.', 'error')
            return render_template('register.html')
        
        if not contrasena:
            flash('La contraseña es requerida.', 'error')
            return render_template('register.html')
        
        # Validar longitud mínima de contraseña
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('register.html')
        
        # Validar que las contraseñas coincidan
        if contrasena != contrasena_confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('register.html')
        
        # Validar formato de correo básico
        if '@' not in correo or '.' not in correo:
            flash('Por favor, ingresa un correo electrónico válido.', 'error')
            return render_template('register.html')

        try:
            # Verificar si el correo ya existe (antes de iniciar la transacción)
            with engine.connect() as conn:
                check_email = text("SELECT Id_Usuario FROM Usuarios WHERE Correo = :correo")
                email_existente = conn.execute(check_email, {"correo": correo}).fetchone()
                
                if email_existente:
                    flash('Este correo electrónico ya está registrado. Por favor, usa otro o inicia sesión.', 'error')
                    return render_template('register.html')
            
            # Obtener el ID del rol Cliente (antes de iniciar la transacción)
            id_rol_cliente = get_rol_id_by_name('Cliente')
            
            # Si no se encuentra el rol 'Cliente', intentar con 'cliente' (minúsculas)
            if not id_rol_cliente:
                id_rol_cliente = get_rol_id_by_name('cliente')
            
            # Si aún no se encuentra, buscar cualquier rol activo como fallback
            if not id_rol_cliente:
                with engine.connect() as conn:
                    fallback_rol = text("SELECT TOP 1 Id_Rol FROM Roles WHERE Estado = 1 ORDER BY Id_Rol")
                    rol_result = conn.execute(fallback_rol).fetchone()
                    if rol_result:
                        id_rol_cliente = rol_result[0]
                    else:
                        flash('Error: No se encontró ningún rol disponible en el sistema.', 'error')
                        return render_template('register.html')
            
            # Hash de la contraseña con bcrypt
            contrasena_bytes = contrasena.encode('utf-8')
            hash_contrasena = bcrypt.hashpw(contrasena_bytes, bcrypt.gensalt())
            
            # Insertar el nuevo usuario (dentro de una transacción)
            with engine.begin() as conn:
                insert_usuario = text("""
                    INSERT INTO Usuarios (Nombre, Correo, Contrasena, Id_Rol, Estado)
                    VALUES (:nombre, :correo, :contrasena, :id_rol, 1)
                """)
                
                conn.execute(insert_usuario, {
                    "nombre": nombre,
                    "correo": correo,
                    "contrasena": hash_contrasena,
                    "id_rol": id_rol_cliente
                })
                
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')
            # ¡IMPORTANTE! Actualizar a la ruta del blueprint
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"Error en registro: {e}")
            flash(f'Error al registrar usuario: {str(e)}', 'error')

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    # ¡IMPORTANTE! Actualizar a la ruta del blueprint
    return redirect(url_for('auth.login'))