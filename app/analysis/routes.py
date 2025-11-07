# app/analysis/routes.py
from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from sqlalchemy import text

# Importamos engine y nuestras funciones de utils
from ..extensions import engine
from ..utils import (
    get_financial_reports, 
    analizar_con_gemini, 
    calcular_analisis_horizontal
)

# Creamos el Blueprint
# No especificamos template_folder para usar el de la app principal
analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/vertical/')
@login_required
def analisis_vertical():
    # ... (Copia tu lógica de /analisis-vertical aquí) ...
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    base_bg = 0
    base_er = 0
    analisis_ia = None
    
    try:
        with engine.connect() as conn:
            # ... (tu lógica para obtener periodos) ...
            if anio_seleccionado:
                report_data = get_financial_reports(anio_seleccionado)
                if report_data:
                    # ... (tu lógica para calcular porcentajes) ...
                    base_bg = report_data['Totales'].get('Total Activo', 0)
                    base_er = report_data['Totales'].get('Ingreso', 0)
                    # ... (resto de tu lógica de cálculo) ...
                    analisis_ia = analizar_con_gemini(report_data, anio_seleccionado, base_bg, base_er)
                else:
                    flash(f'No se encontraron datos para el año {anio_seleccionado}.', 'error')
    except Exception as e:
        print(f"Error en la ruta /analisis-vertical: {e}")
        flash('Error al conectar con la base de datos.', 'error')
        
    return render_template('analisis_vertical.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data,
                           base_bg=base_bg, 
                           base_er=base_er,
                           analisis_ia=analisis_ia)

@analysis_bp.route('/horizontal/')
@login_required
def analisis_horizontal():
    # ... (Copia tu lógica de /analisis-horizontal aquí) ...
    periodo_base = request.args.get('periodo_base', type=int)
    periodo_analisis = request.args.get('periodo_analisis', type=int)
    periodos = []
    analisis_comparativo = None
    
    try:
        with engine.connect() as conn:
            # ... (tu lógica para obtener periodos y datos) ...
            if periodo_base and periodo_analisis and periodo_base < periodo_analisis:
                report_data_base = get_financial_reports(periodo_base)
                report_data_analisis = get_financial_reports(periodo_analisis)
                if report_data_base and report_data_analisis:
                    analisis_comparativo = calcular_analisis_horizontal(report_data_base, report_data_analisis)
                else:
                    flash('No se encontraron datos para uno o ambos períodos.', 'error')
            elif periodo_base and periodo_analisis:
                flash('El período base debe ser menor que el período de análisis.', 'error')
                
    except Exception as e:
        print(f"Error en la ruta /analisis-horizontal: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('analisis_horizontal.html',
                           periodos=periodos,
                           periodo_base=periodo_base,
                           periodo_analisis=periodo_analisis,
                           analisis_comparativo=analisis_comparativo) # Ajusta las variables que pasas

@analysis_bp.route('/ratios-financieros/')
@login_required
def ratios_financieros():
    return "Página de Ratios Financieros - En construcción"

@analysis_bp.route('/origen-aplicacion/')
@login_required
def origen_aplicacion():
    return "Página de Origen y Aplicación - En construcción"