import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

SERVER_NAME = os.getenv('SERVER_NAME', r'(localdb)\Universidad')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'FinanzaDB')
DRIVER_NAME = os.getenv('DRIVER_NAME', 'ODBC Driver 17 for SQL Server')

connection_string = f"mssql+pyodbc://@{SERVER_NAME}/{DATABASE_NAME}?driver={DRIVER_NAME}&trusted_connection=yes"

print(f"Connecting to: {connection_string}")
try:
    engine = create_engine(connection_string)
    
    def run_query(query_str):
        print(f"\nExecuting: {query_str}")
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query_str))
                if result.returns_rows:
                    columns = result.keys()
                    print(f"Columns: {list(columns)}")
                    rows = result.fetchall()
                    if not rows:
                        print("No rows found.")
                    for row in rows:
                        print(row)
                else:
                    print("Query executed successfully (no rows returned).")
        except Exception as e:
            print(f"Error executing query: {e}")

    print("\n--- CatalogoCuentas Structure ---")
    run_query("SELECT TOP 1 * FROM CatalogoCuentas")

    print("\n--- SaldoCuenta Structure ---")
    run_query("SELECT TOP 1 * FROM SaldoCuenta")

    print("\n--- Periodo Structure ---")
    run_query("SELECT * FROM Periodo")

    print("\n--- Distinct TipoCuenta in CatalogoCuentas ---")
    run_query("SELECT DISTINCT TipoCuenta FROM CatalogoCuentas")

    print("\n--- Sum of Balances by Periodo and TipoCuenta ---")
    query = """
    SELECT s.PeriodoID, c.TipoCuenta, SUM(s.Monto) as Total
    FROM SaldoCuenta s
    JOIN CatalogoCuentas c ON s.CuentaID = c.CuentaID
    GROUP BY s.PeriodoID, c.TipoCuenta
    ORDER BY s.PeriodoID, c.TipoCuenta
    """
    run_query(query)

except Exception as e:
    print(f"Failed to connect or create engine: {e}")
