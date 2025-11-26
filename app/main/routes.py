# app/main/routes.py
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import text

# Importamos engine y nuestras funciones de utils
from ..extensions import engine
from ..utils import get_financial_reports, calcular_ratios_financieros

# Creamos el Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/dashboard-cliente')
@login_required
def dashboard_cliente():
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    kpis = {}
    ratios = {}
    report_data_anterior = None
    crecimiento = {}
    
    try:
        with engine.connect() as conn:
            # Obtener todos los períodos disponibles
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if not anio_seleccionado and periodos:
                anio_seleccionado = periodos[0]
            
            if anio_seleccionado:
                # Obtener datos del año actual
                report_data = get_financial_reports(anio_seleccionado)
                
                # Obtener datos del año anterior para comparación
                if len(periodos) > 1 and anio_seleccionado in periodos:
                    indice_actual = periodos.index(anio_seleccionado)
                    if indice_actual < len(periodos) - 1:
                        anio_anterior = periodos[indice_actual + 1]
                        report_data_anterior = get_financial_reports(anio_anterior)
                
                if report_data:
                    # Calcular ratios financieros
                    ratios = calcular_ratios_financieros(report_data, report_data_anterior)
                    
                    # Calcular KPIs importantes para inversores
                    ventas = report_data['Totales'].get('Ingreso', 0.0)
                    utilidad_neta = report_data['Totales'].get('Utilidad Neta', 0.0)
                    utilidad_operativa = report_data['Totales'].get('Utilidad Operativa', 0.0)
                    activos_totales = report_data['Totales'].get('Total Activo', 0.0)
                    patrimonio = report_data['Totales'].get('Total Patrimonio', 0.0)
                    pasivos_totales = report_data['Totales'].get('Total Pasivo', 0.0)
                    
                    # Calcular ROE (Return on Equity)
                    roe = (utilidad_neta / patrimonio * 100) if patrimonio > 0 else 0.0
                    
                    # Calcular ROA (Return on Assets)
                    roa = (utilidad_neta / activos_totales * 100) if activos_totales > 0 else 0.0
                    
                    # Margen de utilidad neta
                    margen_utilidad_neta = (utilidad_neta / ventas * 100) if ventas > 0 else 0.0
                    
                    # Razón circulante
                    activos_circulantes = sum([c['monto'] for c in report_data['Activo'].get('Activo Corriente', [])])
                    pasivos_circulantes = sum([c['monto'] for c in report_data['Pasivo'].get('Pasivo Corriente', [])])
                    razon_circulante = (activos_circulantes / pasivos_circulantes) if pasivos_circulantes > 0 else 0.0
                    
                    # Razón de endeudamiento
                    razon_endeudamiento = ((pasivos_totales / activos_totales) * 100) if activos_totales > 0 else 0.0
                    
                    # Calcular crecimiento si hay datos del año anterior
                    if report_data_anterior:
                        ventas_anterior = report_data_anterior['Totales'].get('Ingreso', 0.0)
                        utilidad_anterior = report_data_anterior['Totales'].get('Utilidad Neta', 0.0)
                        activos_anterior = report_data_anterior['Totales'].get('Total Activo', 0.0)
                        
                        crecimiento_ventas = ((ventas - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0.0
                        crecimiento_utilidad = ((utilidad_neta - utilidad_anterior) / abs(utilidad_anterior) * 100) if utilidad_anterior != 0 else 0.0
                        crecimiento_activos = ((activos_totales - activos_anterior) / activos_anterior * 100) if activos_anterior > 0 else 0.0
                        
                        crecimiento = {
                            'ventas': crecimiento_ventas,
                            'utilidad': crecimiento_utilidad,
                            'activos': crecimiento_activos
                        }
                    
                    kpis = {
                        'ventas': ventas,
                        'utilidad_neta': utilidad_neta,
                        'utilidad_operativa': utilidad_operativa,
                        'activos_totales': activos_totales,
                        'patrimonio': patrimonio,
                        'roa': roa,
                        'roe': roe,
                        'margen_utilidad_neta': margen_utilidad_neta,
                        'razon_circulante': razon_circulante,
                        'razon_endeudamiento': razon_endeudamiento
                    }
    
    except Exception as e:
        print(f"Error en dashboard_cliente: {e}")
        report_data = None
    
    return render_template('dashboard_cliente.html',
                         report_data=report_data,
                         kpis=kpis,
                         ratios=ratios,
                         periodos=periodos,
                         anio_seleccionado=anio_seleccionado,
                         crecimiento=crecimiento)

@main_bp.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    """Endpoint para el chatbot con Gemini"""
    from ..extensions import GEMINI_API_KEY
    import google.generativeai as genai
    
    if not GEMINI_API_KEY:
        return jsonify({'error': 'La API de Gemini no está configurada'}), 500
    
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', '')
        
        if not mensaje:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        # Configurar el modelo - Balance entre potencia, velocidad y costo
        # gemini-2.5-flash: Rápido, potente y económico
        # gemini-1.5-flash: Fallback rápido y económico
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                # Último fallback
                model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # Crear prompt contextual
        prompt = f"""Eres un asistente financiero. Responde de forma PRECISA y CONCISA.

Pregunta del usuario: {mensaje}

REGLAS ESTRICTAS:
1. Responde DIRECTAMENTE la pregunta, sin introducciones largas
2. Máximo 80 palabras - sé breve y al grano
3. Si es sobre un término financiero, da la definición corta (1-2 oraciones)
4. Si es sobre números/análisis, explica QUÉ SIGNIFICA ese número específico
5. NO te extiendas, NO repitas información, NO agregues contexto innecesario
6. Si no sabes algo, di simplemente "No tengo esa información"

Responde SOLO lo que pregunta, de forma directa:"""
        
        response = model.generate_content(prompt)
        
        return jsonify({
            'respuesta': response.text,
            'exito': True
        })
        
    except Exception as e:
        print(f"Error en chatbot: {e}")
        return jsonify({
            'error': f'Error al procesar la consulta: {str(e)}',
            'exito': False
        }), 500

@main_bp.route('/api/all-accounts')
@login_required
def all_accounts():
    try:
        with engine.connect() as conn:
            query = text("SELECT CuentaID, NombreCuenta, TipoCuenta FROM CatalogoCuentas ORDER BY TipoCuenta, NombreCuenta")
            result = conn.execute(query).fetchall()
            accounts = [{'id': row[0], 'name': row[1], 'type': row[2]} for row in result]
            return jsonify(accounts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/account-history')
@login_required
def account_history():
    try:
        account_ids = request.args.getlist('account_ids[]')
        if not account_ids:
            return jsonify({'error': 'No accounts provided'}), 400
            
        # Convert to integers
        account_ids = [int(aid) for aid in account_ids if aid.isdigit()]
        
        if not account_ids:
            return jsonify({'error': 'Invalid account IDs'}), 400
            
        data = {}
        
        with engine.connect() as conn:
            # Get years
            periodos_query = text("SELECT Anio, PeriodoID FROM Periodo ORDER BY Anio ASC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos_map = {row[1]: row[0] for row in periodos_result}
            years = sorted(list(periodos_map.values()))
            
            # Get account names
            placeholders = ','.join([':id' + str(i) for i in range(len(account_ids))])
            params = {f'id{i}': aid for i, aid in enumerate(account_ids)}
            
            names_query = text(f"SELECT CuentaID, NombreCuenta FROM CatalogoCuentas WHERE CuentaID IN ({placeholders})")
            names_result = conn.execute(names_query, params).fetchall()
            # Ensure keys are integers to match account_ids
            account_names = {int(row[0]): row[1] for row in names_result}
            
            # Get balances
            balances_query = text(f"""
                SELECT s.CuentaID, s.PeriodoID, s.Monto 
                FROM SaldoCuenta s 
                WHERE s.CuentaID IN ({placeholders})
            """)
            balances_result = conn.execute(balances_query, params).fetchall()
            
            # Organize data
            # Structure: { 'Account Name': [val_year1, val_year2, ...] }
            
            for aid in account_ids:
                name = account_names.get(aid, f"Account {aid}")
                data[name] = [0.0] * len(years)
                
            for row in balances_result:
                try:
                    aid = int(row[0]) # Ensure integer
                    pid = row[1]
                    monto = float(row[2])
                    
                    if pid in periodos_map:
                        year = periodos_map[pid]
                        year_idx = years.index(year)
                        name = account_names.get(aid)
                        if name and name in data:
                            data[name][year_idx] = monto
                except (ValueError, TypeError) as e:
                    print(f"Skipping row due to type error: {row} - {e}")
                    continue
                        
        return jsonify({
            'years': years,
            'datasets': data
        })
        
    except Exception as e:
        print(f"Error in account_history: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/gestion-reportes')
@login_required
def gestion_reportes():
    from flask import flash
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    
    try:
        with engine.connect() as conn:
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
        print(f"Error en la ruta /gestion-reportes: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('gestion.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data)
