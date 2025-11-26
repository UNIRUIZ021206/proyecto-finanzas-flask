import os
import sys

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.utils import analizar_horizontal_ia

# Mock data for the analysis
report_data_base = {
    'Totales': {
        'Total Activo': 100000,
        'Total Pasivo': 50000,
        'Total Patrimonio': 50000,
        'Ingreso': 20000,
        'Utilidad Neta': 5000
    }
}

report_data_analisis = {
    'Totales': {
        'Total Activo': 120000,
        'Total Pasivo': 60000,
        'Total Patrimonio': 60000,
        'Ingreso': 25000,
        'Utilidad Neta': 7000
    }
}

periodo_base = 2022
periodo_analisis = 2023

print("Testing analizar_horizontal_ia...")
try:
    result = analizar_horizontal_ia(report_data_base, report_data_analisis, periodo_base, periodo_analisis)
    print("\nResult:")
    print(result)
    
    if "Error" in result and "Análisis IA no disponible" not in result:
        print("\nFAILED: The function returned an error message.")
    elif "Análisis IA no disponible" in result:
         print("\nFAILED: The google.generativeai library is not installed or accessible.")
    else:
        print("\nSUCCESS: AI analysis generated successfully.")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
