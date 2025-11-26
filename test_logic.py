from collections import defaultdict

# Mock data based on DB findings
# Row structure: (CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta, Monto)
mock_rows = [
    (1, 'Caja', 'Activo', 'Corriente', 9895003.78),
    (2, 'Deudas', 'Pasivo', 'Corriente', 3031080.27),
    (3, 'Capital', 'Patrimonio', 'Social', 6863923.51),
    (4, 'Ventas', 'Ingreso', 'Operativo', 30812479.51),
    (5, 'Costos', 'Costo', 'Ventas', 16169380.12),
    (6, 'Gastos', 'Gasto', 'Admin', 12721291.66)
]

report_data = {
    'Activo': defaultdict(list),
    'Pasivo': defaultdict(list),
    'Patrimonio': defaultdict(list),
    'Ingreso': defaultdict(list),
    'Costo': defaultdict(list),
    'Gasto': defaultdict(list),
    'Totales': defaultdict(float)
}

print("Processing rows...")
for i, row in enumerate(mock_rows):
    try:
        cuenta = {'id': row[0], 'nombre': row[1], 'monto': 0.0} 
        tipo = str(row[2]).strip() if row[2] else None
        subtipo = str(row[3]).strip() if row[3] else None
        monto_actual = float(row[4]) if row[4] is not None else 0.0
        
        print(f"Row {i}: Tipo='{tipo}', Monto={monto_actual}")

        if not tipo:
            continue
            
        tipo_normalized = tipo.title()
        print(f"  Normalized: '{tipo_normalized}'")
        
        if tipo_normalized not in report_data:
            print(f"  Not in report_data, checking fallbacks...")
            if 'Pasivo' in tipo_normalized:
                tipo_normalized = 'Pasivo'
            elif 'Patrimonio' in tipo_normalized or 'Capital' in tipo_normalized:
                tipo_normalized = 'Patrimonio'
            elif 'Activo' in tipo_normalized:
                tipo_normalized = 'Activo'
            elif 'Ingreso' in tipo_normalized:
                tipo_normalized = 'Ingreso'
            elif 'Costo' in tipo_normalized:
                tipo_normalized = 'Costo'
            elif 'Gasto' in tipo_normalized:
                tipo_normalized = 'Gasto'
            print(f"  Fallback result: '{tipo_normalized}'")
        
        if tipo_normalized not in report_data:
            print(f"Skipping {tipo_normalized}")
            continue
        
        tipo = tipo_normalized
        
        cuenta['monto'] = monto_actual
        if subtipo:
            report_data[tipo][subtipo].append(cuenta)
        report_data['Totales'][tipo] += monto_actual
        if subtipo:
            report_data['Totales'][subtipo] += monto_actual
            
    except Exception as e:
        print(f"Error: {e}")

print("\nCalculating Totales...")
report_data['Totales']['Total Activo'] = report_data['Totales']['Activo']
report_data['Totales']['Total Pasivo'] = report_data['Totales']['Pasivo']
report_data['Totales']['Total Patrimonio'] = report_data['Totales']['Patrimonio']
report_data['Totales']['Total Pasivo y Patrimonio'] = report_data['Totales']['Pasivo'] + report_data['Totales']['Patrimonio']

print(f"Total Activo: {report_data['Totales']['Total Activo']}")
print(f"Total Pasivo: {report_data['Totales']['Total Pasivo']}")
print(f"Total Patrimonio: {report_data['Totales']['Total Patrimonio']}")
print(f"Total Pasivo y Patrimonio: {report_data['Totales']['Total Pasivo y Patrimonio']}")
