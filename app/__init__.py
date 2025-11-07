# app/__init__.py
import os
from flask import Flask
from sqlalchemy import text

# Importamos las extensiones, modelos y utils
from .extensions import engine, login_manager
from .models import User
from .utils import (
    get_rol_name_by_id, 
    is_user_role, 
    is_admin, 
    is_inf
)

def create_app():
    """Crea y configura la instancia de la aplicación Flask."""
    
    # Obtener la ruta base del paquete app
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crear Flask con rutas explícitas para static y templates
    # static_url_path='' asegura que los archivos estáticos se sirvan desde /static
    app = Flask(
        __name__,
        static_folder=os.path.join(app_dir, 'static'),
        static_url_path='/static',
        template_folder=os.path.join(app_dir, 'templates')
    )
    
    # Debug: Verificar que las rutas estén correctas
    print(f"DEBUG: Static folder configurado: {app.static_folder}")
    print(f"DEBUG: Static folder existe: {os.path.exists(app.static_folder)}")
    if os.path.exists(app.static_folder):
        print(f"DEBUG: Archivos en static: {os.listdir(app.static_folder)}")
    
    # --- 1. Configuración ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'una-llave-por-defecto-si-no-hay-env')

    # --- 2. Inicializar Extensiones ---
    login_manager.init_app(app)

    # --- 3. Registrar Blueprints ---
    # Importamos las rutas (Blueprints)
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .admin.routes import admin_bp
    from .analysis.routes import analysis_bp
    
    # Registramos los Blueprints en la app
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp, url_prefix='/') # Opcional, pero claro
    app.register_blueprint(admin_bp, url_prefix='/admin') # Buena idea poner prefijo
    app.register_blueprint(analysis_bp, url_prefix='/analysis') # Buena idea poner prefijo
    
    # --- 4. Registrar User Loader ---
    @login_manager.user_loader
    def load_user(user_id):
        try:
            with engine.connect() as conn:
                query = text("SELECT Id_Usuario, Nombre, Correo, Id_Rol FROM Usuarios WHERE Id_Usuario = :id AND Estado = 1")
                result = conn.execute(query, {"id": int(user_id)}).fetchone()
                if result:
                    return User(id=result[0], nombre=result[1], correo=result[2], id_rol=result[3])
        except Exception as e:
            print(f"Error en user_loader: {e}")
            return None
        return None

    # --- 5. Registrar Filtros de Jinja2 ---
    @app.template_filter('is_inf')
    def is_inf_filter(value):
        return is_inf(value) # Llama a la función de utils

    @app.template_filter('get_rol_name')
    def get_rol_name_filter(id_rol):
        return get_rol_name_by_id(id_rol) # Llama a la función de utils

    # --- 6. Registrar Context Processors ---
    @app.context_processor
    def inject_roles():
        """Inyecta funciones útiles en el contexto de todos los templates"""
        return dict(
            check_user_role=is_user_role,
            get_rol_name=get_rol_name_by_id,
            is_user_admin=is_admin
        )

    return app