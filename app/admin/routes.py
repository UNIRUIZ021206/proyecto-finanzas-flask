# app/admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import text
from decimal import Decimal, InvalidOperation
from collections import defaultdict

# Importamos engine y nuestras funciones de utils
from ..extensions import engine
from ..utils import admin_required, get_financial_reports

# Creamos el Blueprint
# No especificamos template_folder para usar el de la app principal
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/gestion')
@login_required
@admin_required
def gestion():
    # ... (Copia tu lógica de la ruta /gestion aquí) ...
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    
    try:
        with engine.connect() as conn:
            # ... (tu lógica para obtener periodos) ...
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if not anio_seleccionado and periodos:
                anio_seleccionado = periodos[0]
            
            if anio_seleccionado:
                report_data = get_financial_reports(anio_seleccionado)
                if not report_data:
                    flash(f'No se encontraron datos de saldos para el año {anio_seleccionado}.', 'error')

    except Exception as e:
        print(f"Error en la ruta /gestion: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('gestion.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data)

@admin_bp.route('/catalogo-cuentas/', methods=['GET', 'POST'])
@login_required
@admin_required
def catalogo_cuentas():
    if request.method == 'POST':
        # ... (Copia tu lógica POST de /catalogo-cuentas aquí) ...
        try:
            with engine.connect() as conn:
                # ... (tu lógica de validación e INSERT) ...
                flash('Cuenta agregada exitosamente.', 'success')
        except Exception as e:
            print(f"Error en catalogo_cuentas (POST): {e}")
            flash(f'Error al guardar la cuenta: {e}', 'error')
        
        # ¡IMPORTANTE! Actualizar a la ruta del blueprint
        return redirect(url_for('admin.catalogo_cuentas'))

    # --- Lógica GET ---
    cuentas_list = []
    try:
        with engine.connect() as conn:
            # ... (Tu lógica GET para seleccionar cuentas) ...
            query_get = text("SELECT CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta FROM CatalogoCuentas ORDER BY CuentaID")
            cuentas_list = conn.execute(query_get).fetchall()
    except Exception as e:
        print(f"Error en catalogo_cuentas (GET): {e}")
        flash(f'Error al cargar las cuentas: {e}', 'error')

    return render_template('catalogo_cuentas.html', cuentas=cuentas_list)


@admin_bp.route('/ingresar-saldos/', methods=['GET', 'POST'])
@login_required
@admin_required
def ingresar_saldos():
    if request.method == 'POST':
        # ... (Copia tu lógica POST de /ingresar-saldos aquí) ...
        try:
            with engine.begin() as conn:
                # ... (toda tu lógica de transacción, INSERT de período e INSERT de saldos) ...
                pass
            flash(f'Período creado exitosamente con todos sus saldos guardados.', 'success')
            anio_final = request.form.get('anio')
            # ¡IMPORTANTE! Actualizar a la ruta del blueprint
            return redirect(url_for('admin.gestion', anio=anio_final))

        except Exception as e:
            print(f"Error al ingresar saldos (POST): {e}")
            flash(f'Error al guardar los saldos. La operación fue revertida. {e}', 'error')
            # ¡IMPORTANTE! Actualizar a la ruta del blueprint
            return redirect(url_for('admin.ingresar_saldos'))

    # --- Lógica GET ---
    cuentas_agrupadas = defaultdict(lambda: defaultdict(list))
    try:
        with engine.connect() as conn:
            # ... (Tu lógica GET para agrupar cuentas) ...
            pass
    except Exception as e:
        print(f"Error en ingresar_saldos (GET): {e}")
        flash('Error al cargar el catálogo de cuentas.', 'error')

    return render_template('ingresar_saldos.html', 
                           cuentas_agrupadas=cuentas_agrupadas)