import os
from sqlalchemy import create_engine
from flask_login import LoginManager
from dotenv import load_dotenv

# Intentar importar Gemini, con fallback si falla
try:
    import google.generativeai as genai
except ImportError:
    print("ADVERTENCIA: google.generativeai no instalado. Funcionalidades IA deshabilitadas.")
    class MockGenAI:
        def configure(self, api_key): pass
    genai = MockGenAI()

load_dotenv()

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Estamos en Render (Nube)
    # SQLAlchemy moderno necesita 'postgresql://', pero Render a veces da 'postgres://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    connection_string = DATABASE_URL
    print("--- MODO NUBE: Conectando a PostgreSQL ---")
else:
    # Estamos en Local (Tu PC)
    SERVER_NAME = os.getenv('SERVER_NAME', r'(localdb)\Universidad')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'FinanzaDB')
    DRIVER_NAME = os.getenv('DRIVER_NAME', 'ODBC Driver 17 for SQL Server')
    
    connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{DATABASE_NAME}?driver={DRIVER_NAME}&trusted_connection=yes"
    print("--- MODO LOCAL: Conectando a SQL Server ---")

# Crear engine
engine = create_engine(connection_string)

# Configuración Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'error'

# Configuración Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error configuración Gemini: {e}")