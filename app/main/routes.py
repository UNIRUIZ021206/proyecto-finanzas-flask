# app/main/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import text
from ..extensions import engine
from ..utils import is_user_role

# No especificamos template_folder para usar el de la app principal
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Página de Bienvenida (Index) - Redirige según el rol"""
    if is_user_role(current_user.id, 'Cliente') or is_user_role(current_user.id, 'cliente'):
        # ¡IMPORTANTE! Actualizar a la ruta del blueprint
        return redirect(url_for('main.dashboard_cliente'))
    
    return render_template('index.html')

@main_bp.route('/dashboard-cliente')
@login_required
def dashboard_cliente():
    """Dashboard para clientes/inversores"""
    if not (is_user_role(current_user.id, 'Cliente') or is_user_role(current_user.id, 'cliente')):
        flash('No tienes permiso para acceder a esta página.', 'error')
        # ¡IMPORTANTE! Actualizar a la ruta del blueprint
        return redirect(url_for('main.index'))
    
    periodos = []
    try:
        with engine.connect() as conn:
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
    except Exception as e:
        print(f"Error al cargar períodos: {e}")
    
    return render_template('dashboard_cliente.html', periodos=periodos)