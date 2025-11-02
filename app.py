from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, text
from livereload import Server
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from collections import defaultdict # Para organizar los reportes

# --- NUEVO: Integración con Gemini ---
import os
import google.generativeai as genai
from dotenv import load_dotenv
from markdown import markdown # Para convertir la respuesta de Gemini a HTML
import bcrypt

# --- 1. Configuración Inicial ---
app = Flask(__name__)
# ¡MUY IMPORTANTE! Flask-Login necesita una 'secret_key' para firmar las cookies de sesión.
app.config['SECRET_KEY'] = 'esta-es-mi-llave-secreta-y-es-genial'
load_dotenv() # Carga las variables del archivo .env

# --- 2. Configuración de la Conexión a SQL Server ---
# ¡Configuración corregida con tu servidor y BD!
SERVER_NAME = r'(localdb)\Universidad'
DATABASE_NAME = 'FinanzaDB' # <-- SIN la 's'
DRIVER_NAME = 'ODBC Driver 17 for SQL Server'

connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{DATABASE_NAME}?driver={DRIVER_NAME}&trusted_connection=yes"
engine = create_engine(connection_string)

# --- NUEVO: Configuración de la API de Gemini ---
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
    def __init__(self, id, correo, id_rol):
        self.id = id
        self.correo = correo
        self.id_rol = id_rol

@login_manager.user_loader
def load_user(user_id):
    try:
        with engine.connect() as conn:
            query = text("SELECT Id_Usuario, Correo, Id_Rol FROM Usuarios WHERE Id_Usuario = :id AND Estado = 1")
            result = conn.execute(query, {"id": int(user_id)}).fetchone()
            if result:
                return User(id=result[0], correo=result[1], id_rol=result[2])
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

# --- Ruta de Gestión ---

def get_financial_reports(anio_seleccionado):
    """
    Función de ayuda para buscar en la BD y estructurar los datos
    para el Balance General y el Estado de Resultados.
    CORREGIDO: Suma montos sin abs() para manejar contra-cuentas.
    """
    print(f"\n--- Iniciando get_financial_reports para el año: {anio_seleccionado} ---") # DEBUG
    
    report_data = {
        'Activo': defaultdict(list),
        'Pasivo': defaultdict(list),
        'Patrimonio': defaultdict(list),
        'Ingreso': defaultdict(list),
        'Costo': defaultdict(list),
        'Gasto': defaultdict(list),
        'Totales': defaultdict(float) # Usamos defaultdict para inicializar en 0.0
    }
    
    try:
        with engine.connect() as conn:
            # 1. Obtener el PeriodoID
            periodo_query = text("SELECT PeriodoID FROM Periodo WHERE Anio = :anio")
            periodo_result = conn.execute(periodo_query, {"anio": anio_seleccionado}).fetchone()
            
            if not periodo_result:
                print(f"DEBUG: No se encontró PeriodoID para el año {anio_seleccionado}")
                return None

            periodo_id = periodo_result[0]
            print(f"DEBUG: PeriodoID encontrado: {periodo_id}")

            # 2. Obtener saldos y cuentas
            query = text("""
                SELECT 
                    c.CuentaID, c.NombreCuenta, c.TipoCuenta, c.SubTipoCuenta, s.Monto
                FROM SaldoCuenta s
                JOIN CatalogoCuentas c ON s.CuentaID = c.CuentaID
                WHERE s.PeriodoID = :periodo_id
                ORDER BY c.TipoCuenta, c.SubTipoCuenta, c.CuentaID -- Mejor orden
            """)
            
            resultados = conn.execute(query, {"periodo_id": periodo_id}).fetchall()
            
            print(f"DEBUG: Número de saldos encontrados para PeriodoID {periodo_id}: {len(resultados)}")
            if not resultados:
                 print("DEBUG: La consulta de saldos no devolvió resultados.")
                 return None # <-- Si no hay saldos, retornamos None aquí

            # 3. Organizar los datos y CALCULAR TOTALES CORRECTAMENTE
            for i, row in enumerate(resultados):
                # Imprimir las primeras 5 filas para verificar datos
                if i < 5: 
                    print(f"DEBUG: Fila {i}: CuentaID={row[0]}, Monto={row[4]}, Tipo={row[2]}, SubTipo={row[3]}")
                
                cuenta = {'id': row[0], 'nombre': row[1], 'monto': 0.0} # Inicializar monto
                tipo = row[2] 
                subtipo = row[3]
                
                # Convertir a float, manejando None
                monto_actual = float(row[4]) if row[4] is not None else 0.0
                cuenta['monto'] = monto_actual

                # Añadir la cuenta al diccionario anidado
                report_data[tipo][subtipo].append(cuenta)
                
                # *** CORRECCIÓN CLAVE: Sumar SIN abs() ***
                report_data['Totales'][tipo] += monto_actual
                report_data['Totales'][subtipo] += monto_actual

            # Calcular Totales Principales (Ahora serán correctos)
            report_data['Totales']['Total Activo'] = report_data['Totales']['Activo']
            report_data['Totales']['Total Pasivo'] = report_data['Totales']['Pasivo']
            report_data['Totales']['Total Patrimonio'] = report_data['Totales']['Patrimonio']
            report_data['Totales']['Total Pasivo y Patrimonio'] = report_data['Totales']['Pasivo'] + report_data['Totales']['Patrimonio']
            
            # Calcular Utilidades (Ahora serán correctas)
            total_ingresos = report_data['Totales']['Ingreso']
            total_costos = report_data['Totales']['Costo']
            
            utilidad_bruta = total_ingresos - total_costos
            report_data['Totales']['Utilidad Bruta'] = utilidad_bruta
            
            # Corregimos para que la utilidad neta tome en cuenta todos los gastos
            utilidad_neta = utilidad_bruta - report_data['Totales']['Gasto']
            report_data['Totales']['Utilidad Neta'] = utilidad_neta


            print(f"DEBUG: Datos organizados. Total Activo (CORREGIDO): {report_data['Totales']['Total Activo']}") # DEBUG
            print(f"DEBUG: Datos organizados. Total Ingresos: {report_data['Totales']['Ingreso']}") # DEBUG
            return report_data
            
    except Exception as e:
        print(f"Error EXCEPCIÓN en get_financial_reports: {e}")
        return None # <-- Si hay error, retornamos None

@app.route('/gestion')
@login_required
def gestion():
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
                # Si report_data es None (por no encontrar PeriodoID o saldos), flasheamos mensaje
                if not report_data:
                    flash(f'No se encontraron datos de saldos para el año {anio_seleccionado}.', 'error')

    except Exception as e:
        print(f"Error en la ruta /gestion: {e}")
        flash('Error al conectar con la base de datos.', 'error')

    return render_template('gestion.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data)


# --- NUEVO: Función para analizar con Gemini ---
def analizar_con_gemini(report_data, anio, base_bg, base_er):
    """
    Toma los datos del reporte, construye un prompt y obtiene un análisis de Gemini.
    """
    if not GEMINI_API_KEY:
        return "<p><strong>Análisis no disponible:</strong> La clave de API de Gemini no está configurada en el servidor.</p>"

    # Simplificar los datos para el prompt
    prompt_data = f"Análisis Financiero Vertical para el año {anio}:\n\n"
    prompt_data += f"**Balance General (Base 100% = Total Activos: C$ {base_bg:,.2f})**\n"
    
    for tipo in ['Activo', 'Pasivo', 'Patrimonio']:
        if tipo in report_data:
            prompt_data += f"\n*{tipo.upper()}*\n"
            for subtipo, cuentas in report_data[tipo].items():
                # Corregido: 'cuenta' es un diccionario, no un objeto. Usar .get()
                for c in cuentas:
                    percentage = c.get('percentage', 0.0)
                    prompt_data += f"- {c.get('nombre', 'N/A')}: {percentage:.2f}%\n"
                total_subtipo_percent = (report_data['Totales'].get(subtipo, 0.0) / base_bg * 100) if base_bg else 0.0
                prompt_data += f"  - **Total {subtipo}**: {total_subtipo_percent:.2f}%\n"

    prompt_data += f"\n**Estado de Resultados (Base 100% = Ingresos Totales: C$ {base_er:,.2f})**\n"
    
    for tipo in ['Ingreso', 'Costo', 'Gasto']:
        if tipo in report_data:
            prompt_data += f"\n*{tipo.upper()}*\n"
            for subtipo, cuentas in report_data[tipo].items():
                 # Corregido: 'cuenta' es un diccionario, no un objeto. Usar .get()
                 for c in cuentas:
                    percentage = c.get('percentage', 0.0)
                    prompt_data += f"- {c.get('nombre', 'N/A')}: {percentage:.2f}%\n"

    utilidad_bruta_percent = (report_data['Totales'].get('Utilidad Bruta', 0.0) / base_er * 100) if base_er else 0.0
    utilidad_neta_percent = (report_data['Totales'].get('Utilidad Neta', 0.0) / base_er * 100) if base_er else 0.0
    prompt_data += f"\n- **Utilidad Bruta**: {utilidad_bruta_percent:.2f}%\n"
    prompt_data += f"- **Utilidad Neta**: {utilidad_neta_percent:.2f}%\n"

    # El prompt final para la IA
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
        # --- CORRECCIÓN ---
        # El modelo 'gemini-pro' está obsoleto en algunas versiones de la API.
        # Usando el modelo especificado por el usuario.
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt_completo)
        return markdown(response.text) # Convertimos la respuesta a HTML
    except Exception as e:
        print(f"Error al llamar a la API de Gemini: {e}")
        return f"<p><strong>Error al generar el análisis:</strong> {e}</p>"

# --- RUTA PARA ANÁLISIS VERTICAL ---

@app.route('/analisis-vertical/')
@login_required
def analisis_vertical():
    """Página para el Análisis Vertical."""
    
    anio_seleccionado = request.args.get('anio', type=int)
    periodos = []
    report_data = None
    base_bg = 0  
    base_er = 0  
    analisis_ia = None # NUEVO: Variable para el análisis de Gemini
    
    try:
        with engine.connect() as conn:
            # 1. Obtener períodos
            periodos_query = text("SELECT Anio FROM Periodo ORDER BY Anio DESC")
            periodos_result = conn.execute(periodos_query).fetchall()
            periodos = [row[0] for row in periodos_result]
            
            # 2. Seleccionar año
            if not anio_seleccionado and periodos:
                anio_seleccionado = periodos[0]
            
            # 3. Obtener datos
            if anio_seleccionado:
                report_data = get_financial_reports(anio_seleccionado)
                
                if report_data:
                    # 4. CALCULAR ANÁLISIS VERTICAL
                    base_bg = report_data['Totales'].get('Total Activo', 0)
                    base_er = report_data['Totales'].get('Ingreso', 0)
                    print(f"DEBUG AV: Base BG={base_bg}, Base ER={base_er}") # DEBUG Bases

                    # --- CORREGIDO: Añadida verificación de división por cero ---
                    if base_bg > 0:
                        # Calcular % para Balance General
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
                        # Calcular % para Estado de Resultados
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

                    # DEBUG: Imprimir algunos porcentajes calculados (si existen)
                    try:
                        if report_data.get('Activo', {}).get('Activo Corriente', []):
                            print(f"DEBUG AV: % Caja = {report_data['Activo']['Activo Corriente'][0].get('percentage')}")
                    except (IndexError, KeyError) as e:
                        print(f"DEBUG AV: No se pudo imprimir el porcentaje de Caja. {e}")

                    # 5. OBTENER ANÁLISIS DE IA
                    analisis_ia = analizar_con_gemini(report_data, anio_seleccionado, base_bg, base_er)

                # Si get_financial_reports devolvió None, flasheamos mensaje
                else:
                    flash(f'No se encontraron datos de saldos para el año {anio_seleccionado}.', 'error')

    except Exception as e:
        print(f"Error en la ruta /analisis-vertical: {e}")
        flash('Error al conectar con la base de datos.', 'error')

    # Pasamos siempre las variables a la plantilla, aunque report_data sea None
    return render_template('analisis_vertical.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data,
                           base_bg=base_bg, 
                           base_er=base_er,
                           analisis_ia=analisis_ia) # NUEVO: Pasamos el análisis a la plantilla


@app.route('/analisis-horizontal/')
@login_required
def analisis_horizontal():
    return "Página de Análisis Horizontal - En construcción"

@app.route('/ratios-financieros/')
@login_required
def ratios_financieros():
    return "Página de Ratios Financieros - En construcción"

@app.route('/origen-aplicacion/')
@login_required
def origen_aplicacion():
    return "Página de Origen y Aplicación - En construcción"


# --- 6. Ejecución con LiveReload ---
if __name__ == '__main__':
    server = Server(app.wsgi_app)
    server.watch('*.py')
    server.watch('templates/*.html') 
    server.watch('static/*.css')     
    server.serve(port=5000, host='127.0.0.1', debug=True)