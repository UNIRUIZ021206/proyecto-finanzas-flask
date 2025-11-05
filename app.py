from flask import Flask, render_template, request, redirect, url_for, flash
import math
from sqlalchemy import create_engine, text
from livereload import Server
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
from collections import defaultdict # Para organizar los reportes
from decimal import Decimal, InvalidOperation # <-- Importación añadida

# --- Integración con Gemini ---
import os
import google.generativeai as genai
from dotenv import load_dotenv
from markdown import markdown # Para convertir la respuesta de Gemini a HTML
import bcrypt

# --- 1. Configuración Inicial ---
app = Flask(__name__)
load_dotenv() # Carga las variables del archivo .env

# --- Filtro personalizado para Jinja2: verificar si un valor es infinito ---
@app.template_filter('is_inf')
def is_inf(value):
    """Filtro para verificar si un valor es infinito"""
    try:
        return math.isinf(float(value))
    except (ValueError, TypeError):
        return False

# --- CORRECCIÓN DE SEGURIDAD ---
# ¡MUY IMPORTANTE! Leemos la SECRET_KEY desde las variables de entorno.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'una-llave-por-defecto-si-no-hay-env')


# --- 2. Configuración de la Conexión a SQL Server ---
# --- CORRECCIÓN DE CONFIGURACIÓN ---
# Leemos los datos de conexión desde el archivo .env
SERVER_NAME = os.getenv('SERVER_NAME', r'(localdb)\Universidad')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'FinanzaDB')
DRIVER_NAME = os.getenv('DRIVER_NAME', 'ODBC Driver 17 for SQL Server')

connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{DATABASE_NAME}?driver={DRIVER_NAME}&trusted_connection=yes"
engine = create_engine(connection_string)

# --- Configuración de la API de Gemini ---
try:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        print("ADVERTENCIA: La variable de entorno GEMINI_API_KEY no está configurada.")
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error al configurar la API de Gemini: {e}")

# --- 3. Configuración de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

# --- 4. Modelo de Usuario (para Flask-Login) ---
class User(UserMixin):
    def __init__(self, id,nombre, correo, id_rol):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.id_rol = id_rol

@login_manager.user_loader
def load_user(user_id):
    try:
        with engine.connect() as conn:
            # Asumimos que la tabla de usuarios se llama 'Usuarios'
            query = text("SELECT Id_Usuario,Nombre, Correo, Id_Rol FROM Usuarios WHERE Id_Usuario = :id AND Estado = 1")
            result = conn.execute(query, {"id": int(user_id)}).fetchone()
            if result:
                return User(id=result[0], nombre=result[1], correo=result[2], id_rol=result[3])
    except Exception as e:
        print(f"Error en user_loader: {e}")
        return None
    return None

# --- 5. Rutas de la Aplicación ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena_form = request.form.get('contrasena')

        if not correo or not contrasena_form:
            flash('Correo y contraseña son requeridos.', 'error')
            return render_template('login.html')

        try:
            with engine.connect() as conn:
                # Asumimos que la tabla de usuarios se llama 'Usuarios'
                query = text("SELECT Id_Usuario, Correo, Contrasena, Id_Rol FROM Usuarios WHERE Correo = :correo AND Estado = 1")
                result = conn.execute(query, {"correo": correo}).fetchone()

                if result:
                    hash_bd_bytes = result[2]
                    contrasena_form_bytes = contrasena_form.encode('utf-8')

                    if bcrypt.checkpw(contrasena_form_bytes, hash_bd_bytes):
                        usuario_obj = User(id=result[0], correo=result[1], id_rol=result[3])
                        login_user(usuario_obj)
                        return redirect(url_for('index'))
                    else:
                        flash('Correo o contraseña incorrecta.', 'error')
                else:
                    flash('Correo o contraseña incorrecta.', 'error')

        except Exception as e:
            print(f"Error de conexión en login: {e}")
            flash(f'Error al conectar con la base de datos.', 'error')

    return render_template('login.html')

# --- Decorador de Administrador ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Asumimos que el ID_Rol 1 es el Administrador
        if not current_user.is_authenticated or current_user.id_rol != 1:
            flash('No tienes permiso para acceder a esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Página de Bienvenida (Index)"""
    return render_template('index.html')

# --- Ruta de Gestión (Tu nueva función) ---

def get_financial_reports(anio_seleccionado):
    """
    Función de ayuda para buscar en la BD y estructurar los datos
    para el Balance General y el Estado de Resultados.
    (Esta función SÍ COINCIDÍA con tu esquema)
    """
    print(f"\n--- Iniciando get_financial_reports para el año: {anio_seleccionado} ---") # DEBUG
    
    report_data = {
        'Activo': defaultdict(list),
        'Pasivo': defaultdict(list),
        'Patrimonio': defaultdict(list),
        'Ingreso': defaultdict(list),
        'Costo': defaultdict(list),
        'Gasto': defaultdict(list),
        'Totales': defaultdict(float) 
    }
    
    try:
        with engine.connect() as conn:
            # 1. Obtener el PeriodoID (Coincide con tu esquema)
            periodo_query = text("SELECT PeriodoID FROM Periodo WHERE Anio = :anio")
            periodo_result = conn.execute(periodo_query, {"anio": anio_seleccionado}).fetchone()
            
            if not periodo_result:
                print(f"DEBUG: No se encontró PeriodoID para el año {anio_seleccionado}")
                return None

            periodo_id = periodo_result[0]
            print(f"DEBUG: PeriodoID encontrado: {periodo_id}")

            # 2. Obtener saldos y cuentas (Coincide con tu esquema)
            query = text("""
                SELECT 
                    c.CuentaID, c.NombreCuenta, c.TipoCuenta, c.SubTipoCuenta, s.Monto
                FROM SaldoCuenta s
                JOIN CatalogoCuentas c ON s.CuentaID = c.CuentaID
                WHERE s.PeriodoID = :periodo_id
                ORDER BY c.TipoCuenta, c.SubTipoCuenta, c.CuentaID
            """)
            
            resultados = conn.execute(query, {"periodo_id": periodo_id}).fetchall()
            
            print(f"DEBUG: Número de saldos encontrados para PeriodoID {periodo_id}: {len(resultados)}")
            if not resultados:
                 print("DEBUG: La consulta de saldos no devolvió resultados.")
                 return None 

            # 3. Organizar los datos y CALCULAR TOTALES
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


            print(f"DEBUG: Datos organizados. Total Activo: {report_data['Totales']['Total Activo']}") 
            print(f"DEBUG: Datos organizados. Total Ingresos: {report_data['Totales']['Ingreso']}") 
            return report_data
            
    except Exception as e:
        print(f"Error EXCEPCIÓN en get_financial_reports: {e}")
        return None 

@app.route('/gestion')
@login_required
def gestion():
    # Esta ruta es un ejemplo, tú la tienes implementada
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
        print(f"Error en la ruta /gestion: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    # Asumimos que tienes un 'gestion.html'
    return render_template('gestion.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data)


# --- Función para analizar con Gemini ---
def analizar_con_gemini(report_data, anio, base_bg, base_er):
    if not GEMINI_API_KEY:
        return "<p><strong>Análisis no disponible:</strong> La clave de API de Gemini no está configurada en el servidor.</p>"
    
    prompt_data = f"Análisis Financiero Vertical para el año {anio}:\n\n"
    prompt_data += f"**Balance General (Base 100% = Total Activos: C$ {base_bg:,.2f})**\n"
    
    for tipo in ['Activo', 'Pasivo', 'Patrimonio']:
        if tipo in report_data:
            prompt_data += f"\n*{tipo.upper()}*\n"
            for subtipo, cuentas in report_data[tipo].items():
                for c in cuentas:
                    percentage = c.get('percentage', 0.0)
                    prompt_data += f"- {c.get('nombre', 'N/A')}: {percentage:.2f}%\n"
                total_subtipo_percent = (report_data['Totales'].get(subtipo, 0.0) / base_bg * 100) if base_bg else 0.0
                prompt_data += f"   - **Total {subtipo}**: {total_subtipo_percent:.2f}%\n"

    prompt_data += f"\n**Estado de Resultados (Base 100% = Ingresos Totales: C$ {base_er:,.2f})**\n"
    
    for tipo in ['Ingreso', 'Costo', 'Gasto']:
        if tipo in report_data:
            prompt_data += f"\n*{tipo.upper()}*\n"
            for subtipo, cuentas in report_data[tipo].items():
                 for c in cuentas:
                     percentage = c.get('percentage', 0.0)
                     prompt_data += f"- {c.get('nombre', 'N/A')}: {percentage:.2f}%\n"

    utilidad_bruta_percent = (report_data['Totales'].get('Utilidad Bruta', 0.0) / base_er * 100) if base_er else 0.0
    utilidad_neta_percent = (report_data['Totales'].get('Utilidad Neta', 0.0) / base_er * 100) if base_er else 0.0
    prompt_data += f"\n- **Utilidad Bruta**: {utilidad_bruta_percent:.2f}%\n"
    prompt_data += f"- **Utilidad Neta**: {utilidad_neta_percent:.2f}%\n"

    prompt_completo = f"""
    Eres un asistente de análisis financiero experto. A continuación te presento un análisis vertical simplificado de una empresa.
    Tu tarea es generar un resumen ejecutivo conciso (máximo 3 párrafos) que interprete estos datos.

    Enfócate en los puntos más importantes:
    1.  **Estructura de Activos:** ¿La empresa invierte más en activos corrientes o no corrientes? ¿Qué cuenta es la más significativa?
    2.  **Estructura de Financiamiento:** ¿La empresa se financia más con deuda (pasivos) o con capital propio (patrimonio)? ¿Qué tipo de pasivo predomina (corriente o no corriente)?
    3.  **Rentabilidad:** Analiza el margen bruto y el margen neto. ¿Qué tan eficientes son para convertir ingresos en ganancias?
    4.  **Conclusión:** Ofrece una conclusión general sobre la salud financiera de la empresa basada en esta estructura.

    Usa un lenguaje claro y profesional. Formatea tu respuesta usando Markdown con títulos y listas.

    Aquí están los datos:
    ---
    {prompt_data}
    ---
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025') # Modelo actualizado
        response = model.generate_content(prompt_completo)
        return markdown(response.text) 
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return f"<p><strong>Error al generar el análisis:</strong> {e}</p>"

# --- RUTA PARA ANÁLISIS VERTICAL ---

@app.route('/analisis-vertical/')
@login_required
def analisis_vertical():
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    base_bg = 0  
    base_er = 0  
    analisis_ia = None 
    
    try:
        with engine.connect() as conn:
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            if not anio_seleccionado and periodos:
                anio_seleccionado = periodos[0]
            
            if anio_seleccionado:
                report_data = get_financial_reports(anio_seleccionado)
                
                if report_data:
                    base_bg = report_data['Totales'].get('Total Activo', 0)
                    base_er = report_data['Totales'].get('Ingreso', 0)
                    print(f"DEBUG AV: Base BG={base_bg}, Base ER={base_er}")

                    if base_bg > 0:
                        for tipo in ['Activo', 'Pasivo', 'Patrimonio']:
                            if tipo in report_data:
                                for subtipo, cuentas in report_data[tipo].items():
                                    for cuenta in cuentas:
                                        try:
                                            cuenta['percentage'] = (float(cuenta.get('monto', 0.0)) / base_bg) * 100
                                        except (ValueError, TypeError):
                                            cuenta['percentage'] = 0.0
                    else:
                        flash('El Total de Activos es cero, no se puede calcular el análisis vertical del Balance.', 'warning')

                    if base_er > 0:
                        for tipo in ['Ingreso', 'Costo', 'Gasto']:
                            if tipo in report_data:
                                for subtipo, cuentas in report_data[tipo].items():
                                    for cuenta in cuentas:
                                        try:
                                            cuenta['percentage'] = (float(cuenta.get('monto', 0.0)) / base_er) * 100
                                        except (ValueError, TypeError):
                                            cuenta['percentage'] = 0.0
                    else:
                        flash('El Total de Ingresos es cero, no se puede calcular el análisis vertical del E/R.', 'warning')

                    analisis_ia = analizar_con_gemini(report_data, anio_seleccionado, base_bg, base_er)
                else:
                    flash(f'No se encontraron datos de saldos para el año {anio_seleccionado}.', 'error')

    except Exception as e:
        print(f"Error en la ruta /analisis-vertical: {e}")
        flash('Error al conectar con la base de datos.', 'error')

    # Asumimos que tienes un 'analisis_vertical.html'
    return render_template('analisis_vertical.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data,
                           base_bg=base_bg, 
                           base_er=base_er,
                           analisis_ia=analisis_ia) 


@app.route('/analisis-horizontal/')
@login_required
def analisis_horizontal():
    periodo_base = request.args.get('periodo_base', type=int)
    periodo_analisis = request.args.get('periodo_analisis', type=int)
    periodos = []
    report_data_base = None
    report_data_analisis = None
    analisis_comparativo = None
    
    try:
        with engine.connect() as conn:
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            # Validación: el período base debe ser menor que el período de análisis
            if periodo_base and periodo_analisis:
                if periodo_base >= periodo_analisis:
                    flash('El período base debe ser menor que el período de análisis.', 'error')
                    periodo_base = None
                    periodo_analisis = None
                else:
                    # Obtener datos de ambos períodos
                    report_data_base = get_financial_reports(periodo_base)
                    report_data_analisis = get_financial_reports(periodo_analisis)
                    
                    if not report_data_base:
                        flash(f'No se encontraron datos para el período base {periodo_base}.', 'error')
                    elif not report_data_analisis:
                        flash(f'No se encontraron datos para el período de análisis {periodo_analisis}.', 'error')
                    else:
                        # Calcular análisis comparativo
                        analisis_comparativo = calcular_analisis_horizontal(report_data_base, report_data_analisis)
    
    except Exception as e:
        print(f"Error en la ruta /analisis-horizontal: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('analisis_horizontal.html',
                           periodos=periodos,
                           periodo_base=periodo_base,
                           periodo_analisis=periodo_analisis,
                           report_data_base=report_data_base,
                           report_data_analisis=report_data_analisis,
                           analisis_comparativo=analisis_comparativo)


def calcular_analisis_horizontal(report_data_base, report_data_analisis):
    """
    Calcula el análisis horizontal comparando dos períodos.
    Retorna una estructura similar a report_data pero con valores absolutos y relativos.
    """
    analisis = {
        'Activo': defaultdict(list),
        'Pasivo': defaultdict(list),
        'Patrimonio': defaultdict(list),
        'Ingreso': defaultdict(list),
        'Costo': defaultdict(list),
        'Gasto': defaultdict(list),
        'Totales': defaultdict(lambda: {'base': 0.0, 'analisis': 0.0, 'absoluto': 0.0, 'relativo': 0.0})
    }
    
    # Tipos de cuenta a procesar
    tipos_cuenta = ['Activo', 'Pasivo', 'Patrimonio', 'Ingreso', 'Costo', 'Gasto']
    
    for tipo in tipos_cuenta:
        if tipo in report_data_base and tipo in report_data_analisis:
            for subtipo in report_data_base[tipo].keys():
                if subtipo not in report_data_analisis[tipo]:
                    continue
                
                # Obtener cuentas de ambos períodos
                cuentas_base = {cuenta['id']: cuenta for cuenta in report_data_base[tipo][subtipo]}
                cuentas_analisis = {cuenta['id']: cuenta for cuenta in report_data_analisis[tipo][subtipo]}
                
                # Procesar todas las cuentas (pueden existir en uno u otro período)
                todas_las_cuentas = set(cuentas_base.keys()) | set(cuentas_analisis.keys())
                
                for cuenta_id in todas_las_cuentas:
                    monto_base = cuentas_base.get(cuenta_id, {}).get('monto', 0.0)
                    monto_analisis = cuentas_analisis.get(cuenta_id, {}).get('monto', 0.0)
                    
                    # Valor absoluto: período2 - período1
                    valor_absoluto = monto_analisis - monto_base
                    
                    # Valor relativo: ((período2/período1) - 1) * 100
                    if monto_base != 0:
                        valor_relativo = ((monto_analisis / monto_base) - 1) * 100
                    else:
                        # Si el período base es 0, el valor relativo es 0 o infinito
                        valor_relativo = 0.0 if monto_analisis == 0 else float('inf')
                    
                    # Determinar color según el valor relativo
                    if valor_relativo < 0:
                        color_clase = 'valor-negativo'
                    elif valor_relativo > 0:
                        color_clase = 'valor-positivo'
                    else:
                        color_clase = 'valor-cero'
                    
                    cuenta_nombre = cuentas_analisis.get(cuenta_id, cuentas_base.get(cuenta_id, {})).get('nombre', f'Cuenta {cuenta_id}')
                    
                    analisis[tipo][subtipo].append({
                        'id': cuenta_id,
                        'nombre': cuenta_nombre,
                        'monto_base': monto_base,
                        'monto_analisis': monto_analisis,
                        'absoluto': valor_absoluto,
                        'relativo': valor_relativo,
                        'color_clase': color_clase
                    })
    
    # Calcular totales
    for tipo in tipos_cuenta:
        if tipo in report_data_base.get('Totales', {}) and tipo in report_data_analisis.get('Totales', {}):
            total_base = report_data_base['Totales'].get(tipo, 0.0)
            total_analisis = report_data_analisis['Totales'].get(tipo, 0.0)
            total_absoluto = total_analisis - total_base
            if total_base != 0:
                total_relativo = ((total_analisis / total_base) - 1) * 100
            else:
                total_relativo = 0.0 if total_analisis == 0 else float('inf')
            
            if total_relativo < 0:
                color_clase = 'valor-negativo'
            elif total_relativo > 0:
                color_clase = 'valor-positivo'
            else:
                color_clase = 'valor-cero'
            
            analisis['Totales'][tipo] = {
                'base': total_base,
                'analisis': total_analisis,
                'absoluto': total_absoluto,
                'relativo': total_relativo,
                'color_clase': color_clase
            }
    
    # Calcular totales principales (Total Activo, Total Pasivo, etc.)
    if 'Total Activo' in report_data_base['Totales']:
        total_base = report_data_base['Totales']['Total Activo']
        total_analisis = report_data_analisis['Totales']['Total Activo']
        total_absoluto = total_analisis - total_base
        total_relativo = ((total_analisis / total_base) - 1) * 100 if total_base != 0 else 0.0
        analisis['Totales']['Total Activo'] = {
            'base': total_base,
            'analisis': total_analisis,
            'absoluto': total_absoluto,
            'relativo': total_relativo,
            'color_clase': 'valor-positivo' if total_relativo > 0 else ('valor-negativo' if total_relativo < 0 else 'valor-cero')
        }
    
    return analisis

@app.route('/ratios-financieros/')
@login_required
def ratios_financieros():
    return "Página de Ratios Financieros - En construcción"

@app.route('/origen-aplicacion/')
@login_required
def origen_aplicacion():
    return "Página de Origen y Aplicación - En construcción"

# --- RUTA DE CATÁLOGO DE CUENTAS (CORREGIDA PARA TU ESQUEMA) ---

@app.route('/catalogo-cuentas/', methods=['GET', 'POST'])
@login_required
@admin_required # ¡Protegemos la ruta!
def catalogo_cuentas():

    if request.method == 'POST':
        
        # --- CORRECCIÓN DE COHERENCIA DE DATOS ---
        # Leemos los campos que coinciden con tu tabla 'CatalogoCuentas'
        # El formulario enviará 'cuenta_id' (ej: '1101')
        cuenta_id_form = request.form.get('cuenta_id')
        nombre = request.form.get('nombre_cuenta')
        tipo_cuenta = request.form.get('tipo_cuenta')
        subtipo_cuenta = request.form.get('subtipo_cuenta')

        try:
            with engine.connect() as conn:
                if not cuenta_id_form or not nombre or not tipo_cuenta or not subtipo_cuenta:
                    flash('Todos los campos son requeridos.', 'error')
                else:
                    # 1. Verificar que el CuentaID no esté duplicado
                    query_check = text("SELECT CuentaID FROM CatalogoCuentas WHERE CuentaID = :cuenta_id")
                    existe = conn.execute(query_check, {"cuenta_id": cuenta_id_form}).fetchone()

                    if existe:
                        flash(f'El ID de cuenta {cuenta_id_form} ya existe.', 'error')
                    else:
                        # 2. Insertar la nueva cuenta
                        # Las columnas coinciden con tu esquema: CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta
                        query_insert = text("""
                            INSERT INTO CatalogoCuentas (CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta)
                            VALUES (:cuenta_id, :nombre, :tipo_cuenta, :subtipo_cuenta)
                        """)
                        conn.execute(query_insert, {
                            "cuenta_id": cuenta_id_form,
                            "nombre": nombre,
                            "tipo_cuenta": tipo_cuenta,
                            "subtipo_cuenta": subtipo_cuenta
                        })
                        conn.commit()
                        flash('Cuenta agregada exitosamente.', 'success')
                
                return redirect(url_for('catalogo_cuentas'))

        except Exception as e:
            print(f"Error en catalogo_cuentas (POST): {e}")
            flash(f'Error al guardar la cuenta: {e}', 'error')
            return redirect(url_for('catalogo_cuentas'))

    # --- Lógica GET (Cuando cargas la página) ---
    cuentas_list = []
    try:
        with engine.connect() as conn:
            # Leemos las columnas que coinciden con tu esquema
            query_get = text("""
                SELECT CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta 
                FROM CatalogoCuentas 
                ORDER BY CuentaID
            """)
            cuentas_list = conn.execute(query_get).fetchall()

    except Exception as e:
        print(f"Error en catalogo_cuentas (GET): {e}")
        flash(f'Error al cargar las cuentas: {e}', 'error')

    return render_template('catalogo_cuentas.html', cuentas=cuentas_list)


# --- NUEVA RUTA: INGRESAR SALDOS ---

@app.route('/ingresar-saldos/', methods=['GET', 'POST'])
@login_required
@admin_required
def ingresar_saldos():
    
    # --- Lógica POST (Cuando envías el formulario) ---
    if request.method == 'POST':
        anio = request.form.get('anio')
        fecha_cierre = request.form.get('fecha_cierre')

        # Validación: ambos campos son obligatorios
        if not anio or not fecha_cierre:
            flash('El Año y la Fecha de Cierre son requeridos para crear un nuevo período.', 'error')
            return redirect(url_for('ingresar_saldos'))

        # Usamos engine.begin() para una transacción automática (commit o rollback)
        try:
            with engine.begin() as conn:
                # Verificar si el período (año) ya existe
                query_check_periodo = text("SELECT PeriodoID FROM Periodo WHERE Anio = :anio")
                existe = conn.execute(query_check_periodo, {"anio": anio}).fetchone()
                
                if existe:
                    flash(f'El período para el año {anio} ya existe. No se pueden crear períodos duplicados. Los períodos contables son históricos e inmutables.', 'error')
                    return redirect(url_for('ingresar_saldos'))

                # Validar que el año sea razonable
                try:
                    anio_int = int(anio)
                    if anio_int < 2000 or anio_int > 2100:
                        flash('El año debe estar entre 2000 y 2100.', 'error')
                        return redirect(url_for('ingresar_saldos'))
                except (ValueError, TypeError):
                    flash('El año ingresado no es válido. Por favor ingresa un número válido.', 'error')
                    return redirect(url_for('ingresar_saldos'))

                # CREAR EL NUEVO PERÍODO (NUEVO AÑO CONTABLE)
                # Los períodos contables son históricos e inmutables - no se pueden editar
                # Insertar el período
                query_insert_periodo = text("""
                    INSERT INTO Periodo (Anio, FechaCierre) 
                    VALUES (:anio, :fecha_cierre);
                """)
                conn.execute(query_insert_periodo, {"anio": anio, "fecha_cierre": fecha_cierre})
                
                # Obtener el PeriodoID que se acaba de crear usando SCOPE_IDENTITY()
                query_get_new_id = text("SELECT SCOPE_IDENTITY() AS PeriodoID")
                result = conn.execute(query_get_new_id)
                row = result.fetchone()
                
                if not row or not row[0]:
                    # Si SCOPE_IDENTITY() falla, intentamos obtener el ID por el año (fallback)
                    query_fallback = text("SELECT PeriodoID FROM Periodo WHERE Anio = :anio")
                    result_fallback = conn.execute(query_fallback, {"anio": anio})
                    row_fallback = result_fallback.fetchone()
                    if row_fallback and row_fallback[0]:
                        periodo_id_final = int(row_fallback[0])
                    else:
                        raise Exception("No se pudo obtener el nuevo PeriodoID después de crear el período.")
                else:
                    periodo_id_final = int(row[0])
                
                anio_final = anio
                print(f"✅ PERÍODO NUEVO CREADO EXITOSAMENTE: Año {anio_final}, PeriodoID: {periodo_id_final}, Fecha Cierre: {fecha_cierre}")

                # Obtener TODAS las CuentasID del Catálogo
                query_get_cuentas = text("SELECT CuentaID FROM CatalogoCuentas")
                todas_las_cuentas = conn.execute(query_get_cuentas).fetchall()

                # Insertar cada saldo (solo INSERT, no UPDATE - los períodos no se editan)
                query_insert_saldo = text("""
                    INSERT INTO SaldoCuenta (PeriodoID, CuentaID, Monto) 
                    VALUES (:periodo_id, :cuenta_id, :monto)
                """)
                
                for cuenta in todas_las_cuentas:
                    cuenta_id = cuenta[0]
                    form_field_name = f"monto-{cuenta_id}"
                    monto_str = request.form.get(form_field_name, '0').strip()
                    
                    try:
                        monto_decimal = Decimal(monto_str if monto_str else '0.00')
                    except InvalidOperation:
                        monto_decimal = Decimal('0.00')

                    # Insertar el saldo (solo para nuevos períodos)
                    conn.execute(query_insert_saldo, {
                        "periodo_id": periodo_id_final,
                        "cuenta_id": cuenta_id,
                        "monto": monto_decimal
                    })

            # Si todo salió bien, la transacción hace COMMIT aquí
            flash(f'Período {anio_final} creado exitosamente con todos sus saldos guardados.', 'success')
            return redirect(url_for('gestion', anio=anio_final))

        except Exception as e:
            print(f"Error al ingresar saldos (POST): {e}")
            flash(f'Error al guardar los saldos. La operación fue revertida. {e}', 'error')
            return redirect(url_for('ingresar_saldos'))


    # --- Lógica GET (Cuando cargas la página) ---
    cuentas_agrupadas = defaultdict(lambda: defaultdict(list))
    
    try:
        with engine.connect() as conn:
            # Obtener todas las cuentas ordenadas
            query_get = text("""
                SELECT CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta 
                FROM CatalogoCuentas 
                ORDER BY TipoCuenta, SubTipoCuenta, CuentaID
            """)
            cuentas = conn.execute(query_get).fetchall()
            
            # Agrupamos las cuentas para el template
            for cuenta in cuentas:
                cuentas_agrupadas[cuenta.TipoCuenta][cuenta.SubTipoCuenta].append(cuenta)

    except Exception as e:
        print(f"Error en ingresar_saldos (GET): {e}")
        flash('Error al cargar el catálogo de cuentas.', 'error')

    return render_template('ingresar_saldos.html', 
                          cuentas_agrupadas=cuentas_agrupadas)


# --- 6. Ejecución con LiveReload ---
if __name__ == '__main__':
    server = Server(app.wsgi_app)
    server.watch('*.py')
    server.watch('templates/*.html') 
    server.watch('static/*.css')     
    server.serve(port=5000, host='127.0.0.1', debug=True)