import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app import create_app
from app.utils import get_financial_reports

app = create_app()

with app.app_context():
    print("Running get_financial_reports(2023)...")
    data_2023 = get_financial_reports(2023)
    if data_2023:
        print("2023 Totals:", dict(data_2023['Totales']))
    else:
        print("No data for 2023")

    print("\nRunning get_financial_reports(2024)...")
    data_2024 = get_financial_reports(2024)
    if data_2024:
        print("2024 Totals:", dict(data_2024['Totales']))
    else:
        print("No data for 2024")
