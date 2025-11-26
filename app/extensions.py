# app/extensions.py
import os
from sqlalchemy import create_engine
from flask_login import LoginManager
from dotenv import load_dotenv
try:
    import google.generativeai as genai
except ImportError:
    print("ADVERTENCIA: google.generativeai no instalado. Funcionalidades IA deshabilitadas.")
    class MockGenAI:
        def configure(self, api_key): pass
    genai = MockGenAI()

# Carga las variables de entorno ANTES que todo
load_dotenv()

# --- 1. Configuración de la Conexión a SQL Server ---
SERVER_NAME = os.getenv('SERVER_NAME', r'(localdb)\Universidad')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'FinanzaDB')
DRIVER_NAME = os.getenv('DRIVER_NAME', 'ODBC Driver 17 for SQL Server')

connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{DATABASE_NAME}?driver={DRIVER_NAME}&trusted_connection=yes"

# Crea el engine (motor) de la base de datos
engine = create_engine(connection_string)

# --- 2. Configuración de Flask-Login ---
login_manager = LoginManager()
# ¡IMPORTANTE! Apuntar a la nueva ruta del blueprint de autenticación
login_manager.login_view = 'auth.login' 
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

# --- 3. Configuración de la API de Gemini ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("ADVERTENCIA: La variable de entorno GEMINI_API_KEY no está configurada.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error al configurar la API de Gemini: {e}")