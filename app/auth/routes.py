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
        # ... (Copia tu lógica de registro aquí) ...
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        contrasena_confirm = request.form.get('contrasena_confirm')

        # ... (tus validaciones) ...

        try:
            with engine.begin() as conn:
                # ... (tu lógica de checkeo de email) ...
                # ... (tu lógica de hash) ...
                
                id_rol_cliente = get_rol_id_by_name('Cliente')
                # ... (tu lógica de fallback 'cliente') ...
                
                # ... (tu lógica de INSERT) ...
                
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')
            # ¡IMPORTANTE! Actualizar a la ruta del blueprint
            return redirect(url_for('auth.login'))

        except Exception as e:
            print(f"Error en registro: {e}")
            flash(f'Error al registrar usuario: {e}', 'error')

    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    # ¡IMPORTANTE! Actualizar a la ruta del blueprint
    return redirect(url_for('auth.login'))