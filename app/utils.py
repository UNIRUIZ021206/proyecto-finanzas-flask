# app/utils.py
import math
import os
import bcrypt
import google.generativeai as genai
from markdown import markdown
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from sqlalchemy import text
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

# Importamos el engine compartido y la clave de API desde extensions
from .extensions import engine, GEMINI_API_KEY

# --- Filtro personalizado ---
# Nota: El decorador @app.template_filter se aplica en __init__.py
def is_inf(value):
    """Filtro para verificar si un valor es infinito"""
    try:
        return math.isinf(float(value))
    except (ValueError, TypeError):
        return False

# --- Funciones auxiliares para trabajar con Roles ---

def get_rol_id_by_name(nombre_rol):
    """Obtiene el Id_Rol desde la tabla Roles."""
    try:
        with engine.connect() as conn:
            query = text("SELECT Id_Rol FROM Roles WHERE Nombre = :nombre AND Estado = 1")
            result = conn.execute(query, {"nombre": nombre_rol}).fetchone()
            if result:
                return result[0]
    except Exception as e:
        print(f"Error al obtener Id_Rol para {nombre_rol}: {e}")
    return None

def get_rol_name_by_id(id_rol):
    """Obtiene el nombre del rol desde la tabla Roles."""
    try:
        with engine.connect() as conn:
            query = text("SELECT Nombre FROM Roles WHERE Id_Rol = :id_rol AND Estado = 1")
            result = conn.execute(query, {"id_rol": id_rol}).fetchone()
            if result:
                return result[0]
    except Exception as e:
        print(f"Error al obtener nombre de rol para Id_Rol {id_rol}: {e}")
    return None

def is_user_role(user_id, nombre_rol):
    """Verifica si un usuario tiene un rol específico."""
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT COUNT(*) 
                FROM Usuarios u
                INNER JOIN Roles r ON u.Id_Rol = r.Id_Rol
                WHERE u.Id_Usuario = :user_id 
                AND LOWER(r.Nombre) = LOWER(:nombre_rol)
                AND r.Estado = 1 AND u.Estado = 1
            """)
            result = conn.execute(query, {"user_id": user_id, "nombre_rol": nombre_rol}).fetchone()
            return result[0] > 0 if result else False
    except Exception as e:
        print(f"Error al verificar rol {nombre_rol} para usuario {user_id}: {e}")
    return False

def is_admin(user_id):
    """Verifica si un usuario es administrador."""
    if is_user_role(user_id, 'Cliente') or is_user_role(user_id, 'cliente'):
        return False
    
    admin_names = ['Administrador', 'administrador', 'Admin', 'admin', 'Administrator', 'administrator']
    for admin_name in admin_names:
        if is_user_role(user_id, admin_name):
            return True
    
    # Lógica de fallback
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT r.Nombre FROM Usuarios u
                INNER JOIN Roles r ON u.Id_Rol = r.Id_Rol
                WHERE u.Id_Usuario = :user_id AND r.Estado = 1 AND u.Estado = 1
            """)
            result = conn.execute(query, {"user_id": user_id}).fetchone()
            if result:
                return True
    except Exception as e:
        print(f"Error al verificar si es admin para usuario {user_id}: {e}")
    
    return False

# --- Decorador de Administrador ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('No tienes permiso para acceder a esta página.', 'error')
            # ¡IMPORTANTE! Actualizar a la ruta del blueprint
            return redirect(url_for('auth.login')) 
        
        if not is_admin(current_user.id):
            flash('No tienes permiso para acceder a esta página.', 'error')
            # ¡IMPORTANTE! Actualizar a la ruta del blueprint
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

# --- Funciones de Lógica Financiera ---

def get_financial_reports(anio_seleccionado):
    """Función de ayuda para buscar en la BD y estructurar los datos."""
    print(f"\n--- Iniciando get_financial_reports para el año: {anio_seleccionado} ---")
    
    report_data = {
        'Activo': defaultdict(list), 'Pasivo': defaultdict(list),
        'Patrimonio': defaultdict(list), 'Ingreso': defaultdict(list),
        'Costo': defaultdict(list), 'Gasto': defaultdict(list),
        'Totales': defaultdict(float) 
    }
    
    try:
        with engine.connect() as conn:
            periodo_query = text("SELECT PeriodoID FROM Periodo WHERE Anio = :anio")
            periodo_result = conn.execute(periodo_query, {"anio": anio_seleccionado}).fetchone()
            
            if not periodo_result:
                print(f"DEBUG: No se encontró PeriodoID para el año {anio_seleccionado}")
                return None
            periodo_id = periodo_result[0]
            print(f"DEBUG: PeriodoID encontrado: {periodo_id}")

            query = text("""
                SELECT c.CuentaID, c.NombreCuenta, c.TipoCuenta, c.SubTipoCuenta, s.Monto
                FROM SaldoCuenta s
                JOIN CatalogoCuentas c ON s.CuentaID = c.CuentaID
                WHERE s.PeriodoID = :periodo_id
                ORDER BY c.TipoCuenta, c.SubTipoCuenta, c.CuentaID
            """)
            resultados = conn.execute(query, {"periodo_id": periodo_id}).fetchall()
            
            if not resultados:
                print("DEBUG: La consulta de saldos no devolvió resultados.")
                return None 

            for i, row in enumerate(resultados):
                cuenta = {'id': row[0], 'nombre': row[1], 'monto': 0.0} 
                tipo = row[2] 
                subtipo = row[3]
                monto_actual = float(row[4]) if row[4] is not None else 0.0
                cuenta['monto'] = monto_actual
                report_data[tipo][subtipo].append(cuenta)
                report_data['Totales'][tipo] += monto_actual
                report_data['Totales'][subtipo] += monto_actual

            # Calcular Totales Principales
            report_data['Totales']['Total Activo'] = report_data['Totales']['Activo']
            report_data['Totales']['Total Pasivo'] = report_data['Totales']['Pasivo']
            report_data['Totales']['Total Patrimonio'] = report_data['Totales']['Patrimonio']
            report_data['Totales']['Total Pasivo y Patrimonio'] = report_data['Totales']['Pasivo'] + report_data['Totales']['Patrimonio']
            
            # Calcular Utilidades
            total_ingresos = report_data['Totales']['Ingreso']
            total_costos = report_data['Totales']['Costo']
            utilidad_bruta = total_ingresos - total_costos
            report_data['Totales']['Utilidad Bruta'] = utilidad_bruta
            utilidad_neta = utilidad_bruta - report_data['Totales']['Gasto']
            report_data['Totales']['Utilidad Neta'] = utilidad_neta
            
            return report_data
            
    except Exception as e:
        print(f"Error EXCEPCIÓN en get_financial_reports: {e}")
        return None 

def calcular_analisis_horizontal(report_data_base, report_data_analisis):
    """Calcula el análisis horizontal comparando dos períodos."""
    analisis = {
        'Activo': defaultdict(list), 'Pasivo': defaultdict(list),
        'Patrimonio': defaultdict(list), 'Ingreso': defaultdict(list),
        'Costo': defaultdict(list), 'Gasto': defaultdict(list),
        'Totales': defaultdict(lambda: {'base': 0.0, 'analisis': 0.0, 'absoluto': 0.0, 'relativo': 0.0})
    }
    
    tipos_cuenta = ['Activo', 'Pasivo', 'Patrimonio', 'Ingreso', 'Costo', 'Gasto']
    
    for tipo in tipos_cuenta:
        # ... (Copia aquí el resto de tu función calcular_analisis_horizontal) ...
        # (Es muy larga, pero solo necesitas copiarla y pegarla aquí)
        # Asegúrate de que toda la lógica de esa función esté aquí.
        pass # Placeholder para tu lógica
    
    # Ejemplo de la lógica (debes copiar la tuya completa)
    if 'Total Activo' in report_data_base['Totales']:
        total_base = report_data_base['Totales']['Total Activo']
        total_analisis = report_data_analisis['Totales']['Total Activo']
        total_absoluto = total_analisis - total_base
        total_relativo = ((total_analisis / total_base) - 1) * 100 if total_base != 0 else 0.0
        analisis['Totales']['Total Activo'] = {
            'base': total_base, 'analisis': total_analisis,
            'absoluto': total_absoluto, 'relativo': total_relativo,
            'color_clase': 'valor-positivo' if total_relativo > 0 else ('valor-negativo' if total_relativo < 0 else 'valor-cero')
        }
        
    return analisis # Asegúrate de que tu lógica copiada retorne 'analisis'

# --- Función para analizar con Gemini ---
def analizar_con_gemini(report_data, anio, base_bg, base_er):
    if not GEMINI_API_KEY:
        return "<p><strong>Análisis no disponible:</strong> La clave de API de Gemini no está configurada en el servidor.</p>"
    
    # (Copia aquí toda la lógica de tu función analizar_con_gemini)
    # ...
    prompt_data = f"Análisis Financiero Vertical para el año {anio}:\n\n"
    # ... (toda la construcción de tu prompt) ...
    
    prompt_completo = f"""
    Eres un asistente de análisis financiero experto...
    {prompt_data}
    ---
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        response = model.generate_content(prompt_completo)
        return markdown(response.text) 
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return f"<p><strong>Error al generar el análisis:</strong> {e}</p>"