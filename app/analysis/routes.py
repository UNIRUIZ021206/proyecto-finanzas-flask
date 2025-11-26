# app/analysis/routes.py
from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for, jsonify
from flask_login import login_required
from sqlalchemy import text
from io import BytesIO
from datetime import datetime

# Importamos engine y nuestras funciones de utils
from ..extensions import engine
from ..utils import (
    get_financial_reports, 
    analizar_con_gemini,
    analizar_horizontal_ia,
    analizar_ratios_ia,
    analizar_origen_aplicacion_ia,
    analizar_flujo_efectivo_ia,
    calcular_analisis_horizontal,
    calcular_origen_aplicacion,
    calcular_ratios_financieros,
    exportar_analisis_excel,
    calcular_ctno,
    calcular_feo_indirecto,
    calcular_estado_flujo_efectivo,
    generar_analisis_dupont,
    generar_estado_proforma
)

# Creamos el Blueprint
# No especificamos template_folder para usar el de la app principal
analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/vertical/')
@login_required
def analisis_vertical():
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    base_bg = 0
    base_er = 0
    analisis_ia = None
    ctno_data = None
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if anio_seleccionado:
                report_data = get_financial_reports(anio_seleccionado)
                if report_data:
                    base_bg = report_data['Totales'].get('Total Activo', 0)
                    base_er = report_data['Totales'].get('Ingreso', 0)
                    
                    # Calcular porcentajes verticales para cada cuenta
                    tipos_balance = ['Activo', 'Pasivo', 'Patrimonio']
                    tipos_resultados = ['Ingreso', 'Costo', 'Gasto']
                    
                    # Para Balance General (base = Total Activo)
                    for tipo in tipos_balance:
                        for subtipo, cuentas in report_data[tipo].items():
                            for cuenta in cuentas:
                                if base_bg > 0:
                                    cuenta['percentage'] = (cuenta['monto'] / base_bg) * 100
                                else:
                                    cuenta['percentage'] = 0.0
                    
                    # Para Estado de Resultados (base = Ingresos)
                    for tipo in tipos_resultados:
                        for subtipo, cuentas in report_data[tipo].items():
                            for cuenta in cuentas:
                                if base_er > 0:
                                    cuenta['percentage'] = (cuenta['monto'] / base_er) * 100
                                else:
                                    cuenta['percentage'] = 0.0
                    
                    # analisis_ia = analizar_con_gemini(report_data, anio_seleccionado)
                    # Ahora se carga vía AJAX
                    analisis_ia = None
                    
                    # Calcular CTNO (Capital de Trabajo Neto Operativo)
                    ctno_data = calcular_ctno(anio_seleccionado)
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
                           analisis_ia=analisis_ia,
                           ctno_data=ctno_data)

@analysis_bp.route('/horizontal/')
@login_required
def analisis_horizontal():
    periodo_base = request.args.get('periodo_base', type=int)
    periodo_analisis = request.args.get('periodo_analisis', type=int)
    periodos = []
    analisis_comparativo = None
    report_data_base = None
    report_data_analisis = None
    analisis_ia = None
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if periodo_base and periodo_analisis:
                if periodo_base < periodo_analisis:
                    report_data_base = get_financial_reports(periodo_base)
                    report_data_analisis = get_financial_reports(periodo_analisis)
                    if report_data_base and report_data_analisis:
                        analisis_comparativo = calcular_analisis_horizontal(report_data_base, report_data_analisis)
                        # Agregar análisis con IA (ahora vía AJAX)
                        analisis_ia = None
                    else:
                        flash('No se encontraron datos para uno o ambos períodos.', 'error')
                else:
                    flash('El período base debe ser menor que el período de análisis.', 'error')
                
    except Exception as e:
        print(f"Error en la ruta /analisis-horizontal: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('analisis_horizontal.html',
                           periodos=periodos,
                           periodo_base=periodo_base,
                           periodo_analisis=periodo_analisis,
                           analisis_comparativo=analisis_comparativo,
                           report_data_base=report_data_base,
                           report_data_analisis=report_data_analisis,
                           analisis_ia=analisis_ia)

@analysis_bp.route('/ratios-financieros/')
@login_required
def ratios_financieros():
    anio_seleccionado = request.args.get('anio', type=int)
    anio_anterior = request.args.get('anio_anterior', type=int)
    periodos = []
    ratios_data = None
    report_data_anio = None
    report_data_anio_anterior = None
    analisis_ia = None
    dupont_data = None
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if anio_seleccionado:
                report_data_anio = get_financial_reports(anio_seleccionado)
                if report_data_anio:
                    # Si se proporciona año anterior, obtener esos datos también
                    if anio_anterior:
                        report_data_anio_anterior = get_financial_reports(anio_anterior)
                    
                    # Calcular ratios financieros
                    ratios_data = calcular_ratios_financieros(report_data_anio, report_data_anio_anterior)
                    ratios_data['anio'] = anio_seleccionado
                    ratios_data['anio_anterior'] = anio_anterior
                    
                    # Calcular Análisis DuPont
                    dupont_result = generar_analisis_dupont(anio_seleccionado)
                    if dupont_result.get('exito'):
                        dupont_data = dupont_result.get('analisis_dupont')
                    
                    # Agregar análisis con IA (ahora vía AJAX)
                    analisis_ia = None
                else:
                    flash(f'No se encontraron datos para el año {anio_seleccionado}.', 'error')
                
    except Exception as e:
        print(f"Error en la ruta /ratios-financieros: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('ratios_financieros.html',
                           periodos=periodos,
                           anio_seleccionado=anio_seleccionado,
                           anio_anterior=anio_anterior,
                           ratios_data=ratios_data,
                           report_data_anio=report_data_anio,
                           report_data_anio_anterior=report_data_anio_anterior,
                           analisis_ia=analisis_ia,
                           dupont_data=dupont_data)

@analysis_bp.route('/origen-aplicacion/')
@login_required
def origen_aplicacion():
    periodo_base = request.args.get('periodo_base', type=int)
    periodo_analisis = request.args.get('periodo_analisis', type=int)
    periodos = []
    origen_aplicacion_data = None
    report_data_base = None
    report_data_analisis = None
    analisis_ia = None
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if periodo_base and periodo_analisis:
                if periodo_base < periodo_analisis:
                    report_data_base = get_financial_reports(periodo_base)
                    report_data_analisis = get_financial_reports(periodo_analisis)
                    if report_data_base and report_data_analisis:
                        origen_aplicacion_data = calcular_origen_aplicacion(report_data_base, report_data_analisis)
                        # Agregar análisis con IA (ahora vía AJAX)
                        analisis_ia = None
                    else:
                        flash('No se encontraron datos para uno o ambos períodos.', 'error')
                else:
                    flash('El período base debe ser menor que el período de análisis.', 'error')
                
    except Exception as e:
        print(f"Error en la ruta /origen-aplicacion: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('origen_aplicacion.html',
                           periodos=periodos,
                           periodo_base=periodo_base,
                           periodo_analisis=periodo_analisis,
                           origen_aplicacion_data=origen_aplicacion_data,
                           report_data_base=report_data_base,
                           report_data_analisis=report_data_analisis,
                           analisis_ia=analisis_ia)

@analysis_bp.route('/flujo-efectivo/')
@login_required
def flujo_efectivo():
    periodo_inicio = request.args.get('periodo_inicio', type=int)
    periodo_fin = request.args.get('periodo_fin', type=int)
    flujo_data = None
    feo_data = None
    periodos = []
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles para mostrar en el selector
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if periodo_inicio and periodo_fin:
                if periodo_inicio < periodo_fin:
                    # Calcular Estado de Flujo de Efectivo (clasificado cuenta por cuenta)
                    flujo_data = calcular_estado_flujo_efectivo(periodo_inicio, periodo_fin)
                    if not flujo_data['exito']:
                        flash(flujo_data['mensaje'], 'error')
                    
                    # También calcular FEO para mostrar el resumen
                    fecha_inicio = f"{periodo_inicio}-01-01"
                    fecha_fin = f"{periodo_fin}-12-31"
                    feo_data = calcular_feo_indirecto(fecha_inicio, fecha_fin)
                else:
                    flash('El período de inicio debe ser menor que el período de fin.', 'error')
            elif periodo_inicio or periodo_fin:
                flash('Por favor, selecciona ambos períodos (inicio y fin) para calcular el Flujo de Efectivo.', 'warning')
                
    except Exception as e:
        print(f"Error en la ruta /flujo-efectivo: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('flujo_efectivo.html',
                           periodos=periodos,
                           periodo_inicio=periodo_inicio,
                           periodo_fin=periodo_fin,
                           flujo_data=flujo_data,
                           feo_data=feo_data)

@analysis_bp.route('/proforma/')
@login_required
def proforma():
    anio_base = request.args.get('anio_base', type=int)
    tasa_crecimiento = request.args.get('tasa_crecimiento', type=float)
    periodos = []
    proforma_data = None
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if anio_base and tasa_crecimiento is not None:
                report_data = get_financial_reports(anio_base)
                if report_data:
                    # Convertir porcentaje a decimal (ej. 15 -> 0.15)
                    tasa_decimal = tasa_crecimiento / 100.0
                    
                    resultado = generar_estado_proforma(report_data, tasa_decimal)
                    if resultado['exito']:
                        proforma_data = resultado['proforma']
                    else:
                        flash(resultado['mensaje'], 'error')
                else:
                    flash(f'No se encontraron datos para el año {anio_base}.', 'error')
            elif anio_base:
                flash('Por favor, ingresa una tasa de crecimiento.', 'warning')
                
    except Exception as e:
        print(f"Error en la ruta /proforma: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('proforma.html',
                           periodos=periodos,
                           anio_base=anio_base,
                           tasa_crecimiento=tasa_crecimiento,
                           proforma_data=proforma_data)

@analysis_bp.route('/exportar-excel')
@login_required
def exportar_excel():
    """Exporta el análisis financiero calculado a Excel"""
    try:
        tipo_analisis = request.args.get('tipo', 'vertical')  # vertical, horizontal, ratios, origen_aplicacion
        anio_seleccionado = request.args.get('anio', type=int)
        periodo_base = request.args.get('periodo_base', type=int)
        periodo_analisis = request.args.get('periodo_analisis', type=int)
        
        wb = None
        
        if tipo_analisis == 'vertical':
            if not anio_seleccionado:
                flash('Debe seleccionar un año para exportar.', 'error')
                return redirect(url_for('analysis.analisis_vertical'))
            report_data = get_financial_reports(anio_seleccionado)
            if not report_data:
                flash('No se encontraron datos para exportar.', 'error')
                return redirect(url_for('analysis.analisis_vertical'))
            from ..utils import exportar_analisis_vertical_excel
            wb = exportar_analisis_vertical_excel(anio_seleccionado, report_data)
            nombre_base = f'Analisis_Vertical_{anio_seleccionado}'
        
        elif tipo_analisis == 'horizontal':
            if not periodo_base or not periodo_analisis:
                flash('Debe seleccionar ambos períodos para exportar.', 'error')
                return redirect(url_for('analysis.analisis_horizontal'))
            report_data_base = get_financial_reports(periodo_base)
            report_data_analisis = get_financial_reports(periodo_analisis)
            if not report_data_base or not report_data_analisis:
                flash('No se encontraron datos para exportar.', 'error')
                return redirect(url_for('analysis.analisis_horizontal'))
            analisis_comparativo = calcular_analisis_horizontal(report_data_base, report_data_analisis)
            from ..utils import exportar_analisis_horizontal_excel
            wb = exportar_analisis_horizontal_excel(periodo_base, periodo_analisis, analisis_comparativo)
            nombre_base = f'Analisis_Horizontal_{periodo_base}_{periodo_analisis}'
        
        elif tipo_analisis == 'ratios':
            if not anio_seleccionado:
                flash('Debe seleccionar un año para exportar.', 'error')
                return redirect(url_for('analysis.ratios_financieros'))
            report_data = get_financial_reports(anio_seleccionado)
            if not report_data:
                flash('No se encontraron datos para exportar.', 'error')
                return redirect(url_for('analysis.ratios_financieros'))
            # Obtener año anterior para ratios si es necesario
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            with engine.connect() as conn:
                periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            report_data_anterior = None
            if anio_seleccionado in periodos:
                idx = periodos.index(anio_seleccionado)
                if idx + 1 < len(periodos):
                    report_data_anterior = get_financial_reports(periodos[idx + 1])
            ratios_data = calcular_ratios_financieros(report_data, report_data_anterior)
            from ..utils import exportar_ratios_excel
            wb = exportar_ratios_excel(anio_seleccionado, ratios_data)
            nombre_base = f'Ratios_Financieros_{anio_seleccionado}'
        
        elif tipo_analisis == 'origen_aplicacion':
            if not periodo_base or not periodo_analisis:
                flash('Debe seleccionar ambos períodos para exportar.', 'error')
                return redirect(url_for('analysis.origen_aplicacion'))
            report_data_base = get_financial_reports(periodo_base)
            report_data_analisis = get_financial_reports(periodo_analisis)
            if not report_data_base or not report_data_analisis:
                flash('No se encontraron datos para exportar.', 'error')
                return redirect(url_for('analysis.origen_aplicacion'))
            origen_aplicacion_data = calcular_origen_aplicacion(report_data_base, report_data_analisis)
            from ..utils import exportar_origen_aplicacion_excel
            wb = exportar_origen_aplicacion_excel(periodo_base, periodo_analisis, origen_aplicacion_data)
            nombre_base = f'Origen_Aplicacion_{periodo_base}_vs_{periodo_analisis}'
        
        if not wb:
            flash('No se encontraron datos para exportar.', 'error')
            return redirect(url_for('main.index'))
        
        # Guardar el workbook en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generar nombre de archivo
        fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f'{nombre_base}_{fecha}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nombre_archivo
        )
        
    except Exception as e:
        print(f"Error al exportar a Excel: {e}")
        flash('Error al generar el archivo Excel. Por favor, intenta de nuevo.', 'error')
        return redirect(url_for('main.index'))

# --- API Endpoints para Análisis con IA (Carga Asíncrona) ---

@analysis_bp.route('/api/vertical-ia/<int:anio>')
@login_required
def api_vertical_ia(anio):
    try:
        report_data = get_financial_reports(anio)
        if not report_data:
            return jsonify({'error': 'No se encontraron datos'}), 404
            
        # Calcular porcentajes verticales (necesario para el contexto de la IA)
        base_bg = report_data['Totales'].get('Total Activo', 0)
        base_er = report_data['Totales'].get('Ingreso', 0)
        
        tipos_balance = ['Activo', 'Pasivo', 'Patrimonio']
        tipos_resultados = ['Ingreso', 'Costo', 'Gasto']
        
        for tipo in tipos_balance:
            for subtipo, cuentas in report_data[tipo].items():
                for cuenta in cuentas:
                    if base_bg > 0:
                        cuenta['percentage'] = (cuenta['monto'] / base_bg) * 100
                    else:
                        cuenta['percentage'] = 0.0
        
        for tipo in tipos_resultados:
            for subtipo, cuentas in report_data[tipo].items():
                for cuenta in cuentas:
                    if base_er > 0:
                        cuenta['percentage'] = (cuenta['monto'] / base_er) * 100
                    else:
                        cuenta['percentage'] = 0.0
                        
        analisis_html = analizar_con_gemini(report_data, anio)
        return jsonify({'html': analisis_html})
    except Exception as e:
        print(f"Error en API Vertical IA: {e}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/horizontal-ia')
@login_required
def api_horizontal_ia():
    try:
        periodo_base = request.args.get('base', type=int)
        periodo_analisis = request.args.get('analisis', type=int)
        
        if not periodo_base or not periodo_analisis:
            return jsonify({'error': 'Faltan parámetros'}), 400
            
        report_data_base = get_financial_reports(periodo_base)
        report_data_analisis = get_financial_reports(periodo_analisis)
        
        if not report_data_base or not report_data_analisis:
            return jsonify({'error': 'No se encontraron datos'}), 404
            
        # No necesitamos calcular todo el comparativo detallado si la IA usa los reportes crudos,
        # pero analizar_horizontal_ia usa los reportes base y analisis.
        analisis_html = analizar_horizontal_ia(report_data_base, report_data_analisis, periodo_base, periodo_analisis)
        return jsonify({'html': analisis_html})
    except Exception as e:
        print(f"Error en API Horizontal IA: {e}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/ratios-ia')
@login_required
def api_ratios_ia():
    try:
        anio = request.args.get('anio', type=int)
        anio_anterior = request.args.get('anio_anterior', type=int)
        
        if not anio:
            return jsonify({'error': 'Falta el año'}), 400
            
        report_data = get_financial_reports(anio)
        if not report_data:
            return jsonify({'error': 'No se encontraron datos'}), 404
            
        report_data_anterior = None
        if anio_anterior:
            report_data_anterior = get_financial_reports(anio_anterior)
            
        ratios_data = calcular_ratios_financieros(report_data, report_data_anterior)
        ratios_data['anio'] = anio
        ratios_data['anio_anterior'] = anio_anterior
        
        analisis_html = analizar_ratios_ia(ratios_data)
        return jsonify({'html': analisis_html})
    except Exception as e:
        print(f"Error en API Ratios IA: {e}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/origen-aplicacion-ia')
@login_required
def api_origen_aplicacion_ia():
    try:
        periodo_base = request.args.get('base', type=int)
        periodo_analisis = request.args.get('analisis', type=int)
        
        if not periodo_base or not periodo_analisis:
            return jsonify({'error': 'Faltan parámetros'}), 400
            
        report_data_base = get_financial_reports(periodo_base)
        report_data_analisis = get_financial_reports(periodo_analisis)
        
        if not report_data_base or not report_data_analisis:
            return jsonify({'error': 'No se encontraron datos'}), 404
            
        origen_aplicacion_data = calcular_origen_aplicacion(report_data_base, report_data_analisis)
        
        analisis_html = analizar_origen_aplicacion_ia(origen_aplicacion_data)
        return jsonify({'html': analisis_html})
    except Exception as e:
        print(f"Error en API Origen Aplicación IA: {e}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/flujo-efectivo-ia')
@login_required
def api_flujo_efectivo_ia():
    try:
        periodo_inicio = request.args.get('inicio', type=int)
        periodo_fin = request.args.get('fin', type=int)
        
        if not periodo_inicio or not periodo_fin:
            return jsonify({'error': 'Faltan parámetros'}), 400
            
        # Recalcular datos de flujo (necesario para la IA)
        flujo_data = calcular_estado_flujo_efectivo(periodo_inicio, periodo_fin)
        
        if not flujo_data or not flujo_data.get('exito'):
             return jsonify({'error': 'No se pudieron calcular los datos'}), 404

        analisis_html = analizar_flujo_efectivo_ia(flujo_data, periodo_inicio, periodo_fin)
        return jsonify({'html': analisis_html})
    except Exception as e:
        print(f"Error en API Flujo Efectivo IA: {e}")
        return jsonify({'error': str(e)}), 500
