# app/admin/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import text
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from datetime import date

# Importamos engine y nuestras funciones de utils
from ..extensions import engine
from ..utils import admin_required, get_financial_reports

# Creamos el Blueprint
# No especificamos template_folder para usar el de la app principal
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/gestion')
@login_required
@admin_required
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
                if not report_data:
                    flash(f'No se encontraron datos de saldos para el año {anio_seleccionado}.', 'error')

    except Exception as e:
        print(f"Error en la ruta /gestion: {e}")
        flash('Error al conectar con la base de datos.', 'error')
    
    return render_template('gestion.html', 
                           periodos=periodos, 
                           anio_seleccionado=anio_seleccionado,
                           report_data=report_data)

@admin_bp.route('/catalogo-cuentas/', methods=['GET', 'POST'])
@login_required
@admin_required
def catalogo_cuentas():
    if request.method == 'POST':
        cuenta_id = request.form.get('cuenta_id')
        nombre = request.form.get('nombre')
        tipo = request.form.get('tipo')
        subtipo = request.form.get('subtipo')
        
        if not cuenta_id:
            flash('El ID de cuenta es requerido.', 'error')
            return redirect(url_for('admin.catalogo_cuentas'))
        
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO CatalogoCuentas (CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta) VALUES (:cuenta_id, :nombre, :tipo, :subtipo)"),
                    {"cuenta_id": cuenta_id, "nombre": nombre, "tipo": tipo, "subtipo": subtipo}
                )
                flash('Cuenta agregada exitosamente.', 'success')
        except Exception as e:
            print(f"Error en catalogo_cuentas (POST): {e}")
            flash(f'Error al guardar la cuenta: {e}', 'error')
        
        return redirect(url_for('admin.catalogo_cuentas'))

    # --- Lógica GET ---
    cuentas_list = []
    try:
        with engine.connect() as conn:
            query_get = text("SELECT CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta FROM CatalogoCuentas ORDER BY CuentaID")
            cuentas_list = conn.execute(query_get).fetchall()
    except Exception as e:
        print(f"Error en catalogo_cuentas (GET): {e}")
        flash(f'Error al cargar las cuentas: {e}', 'error')

    return render_template('catalogo_cuentas.html', cuentas=cuentas_list)


@admin_bp.route('/ingresar-saldos/', methods=['GET', 'POST'])
@login_required
@admin_required
def ingresar_saldos():
    if request.method == 'POST':
        anio = request.form.get('anio')
        
        try:
            with engine.begin() as conn:
                # Verificar si el periodo existe, si no crearlo
                periodo_query = text("SELECT PeriodoID FROM Periodo WHERE Anio = :anio")
                periodo_result = conn.execute(periodo_query, {"anio": anio}).fetchone();
                
                if not periodo_result:
                    # PostgreSQL: Agregar FechaCierre requerido
                    fecha_cierre = date(int(anio), 12, 31)
                    conn.execute(
                        text("INSERT INTO Periodo (Anio, FechaCierre) VALUES (:anio, :fecha_cierre)"), 
                        {"anio": anio, "fecha_cierre": fecha_cierre}
                    )
                    periodo_result = conn.execute(periodo_query, {"anio": anio}).fetchone()
                
                periodo_id = periodo_result[0]
                
                # Procesar saldos
                for key, value in request.form.items():
                    if key.startswith('saldo_'):
                        cuenta_id = key.split('_')[1]
                        monto = value
                        if monto:
                            # PostgreSQL: INSERT ... ON CONFLICT (reemplaza MERGE)
                            conn.execute(text("""
                                INSERT INTO SaldoCuenta (CuentaID, PeriodoID, Monto)
                                VALUES (:cuenta_id, :periodo_id, :monto)
                                ON CONFLICT (PeriodoID, CuentaID)
                                DO UPDATE SET Monto = EXCLUDED.Monto
                            """), {"cuenta_id": cuenta_id, "periodo_id": periodo_id, "monto": monto})

            flash(f'Saldos guardados exitosamente para el año {anio}.', 'success')
            return redirect(url_for('admin.gestion', anio=anio))

        except Exception as e:
            print(f"Error al ingresar saldos (POST): {e}")
            flash(f'Error al guardar los saldos: {e}', 'error')
            return redirect(url_for('admin.ingresar_saldos'))

    # --- Lógica GET ---
    cuentas_agrupadas = defaultdict(lambda: defaultdict(list))
    try:
        with engine.connect() as conn:
            query = text("SELECT CuentaID, NombreCuenta, TipoCuenta, SubTipoCuenta FROM CatalogoCuentas ORDER BY TipoCuenta, SubTipoCuenta, NombreCuenta")
            cuentas = conn.execute(query).fetchall()
            
            for cuenta in cuentas:
                cuentas_agrupadas[cuenta.TipoCuenta][cuenta.SubTipoCuenta].append(cuenta)
                
    except Exception as e:
        print(f"Error en ingresar_saldos (GET): {e}")
        flash('Error al cargar el catálogo de cuentas.', 'error')

    return render_template('ingresar_saldos.html', 
                           cuentas_agrupadas=cuentas_agrupadas)

@admin_bp.route('/gestion-usuarios')
@login_required
@admin_required
def gestion_usuarios():
    users = []
    roles = []
    try:
        with engine.connect() as conn:
            # Fetch users with their roles
            query_users = text("""
                SELECT u.Id_Usuario, u.Nombre, u.Correo, r.Nombre as Rol, u.Estado, u.Id_Rol
                FROM Usuarios u
                JOIN Roles r ON u.Id_Rol = r.Id_Rol
                ORDER BY u.Nombre
            """)
            users = conn.execute(query_users).fetchall()
            
            # Fetch all available roles for the dropdown/modal
            query_roles = text("SELECT Id_Rol, Nombre FROM Roles WHERE Estado = 1")
            roles = conn.execute(query_roles).fetchall()
            
    except Exception as e:
        print(f"Error en gestion_usuarios: {e}")
        flash('Error al cargar usuarios.', 'error')
        
    return render_template('gestion_usuarios.html', users=users, roles=roles)

@admin_bp.route('/update-user-role', methods=['POST'])
@login_required
@admin_required
def update_user_role():
    user_id = request.form.get('user_id')
    new_role_id = request.form.get('role_id')
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE Usuarios SET Id_Rol = :role_id WHERE Id_Usuario = :user_id"),
                {"role_id": new_role_id, "user_id": user_id}
            )
        flash('Rol de usuario actualizado correctamente.', 'success')
    except Exception as e:
        print(f"Error updating user role: {e}")
        flash('Error al actualizar el rol.', 'error')
        
    return redirect(url_for('admin.gestion_usuarios'))

@admin_bp.route('/toggle-user-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status():
    user_id = request.form.get('user_id')
    
    try:
        with engine.begin() as conn:
            # Get current status
            current_status = conn.execute(
                text("SELECT Estado FROM Usuarios WHERE Id_Usuario = :id"),
                {"id": user_id}
            ).scalar()
            
            new_status = 0 if current_status == 1 else 1
            
            conn.execute(
                text("UPDATE Usuarios SET Estado = :status WHERE Id_Usuario = :id"),
                {"status": new_status, "id": user_id}
            )
            
        flash('Estado de usuario actualizado correctamente.', 'success')
    except Exception as e:
        print(f"Error updating user status: {e}")
        flash('Error al actualizar el estado.', 'error')
        
    return redirect(url_for('admin.gestion_usuarios'))

@admin_bp.route('/catalogo-cuentas/editar', methods=['POST'])
@login_required
@admin_required
def editar_cuenta():
    cuenta_id = request.form.get('cuenta_id')
    nombre = request.form.get('nombre_cuenta')
    tipo = request.form.get('tipo_cuenta')
    subtipo = request.form.get('subtipo_cuenta')
    
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE CatalogoCuentas SET NombreCuenta = :nombre, TipoCuenta = :tipo, SubTipoCuenta = :subtipo WHERE CuentaID = :id"),
                {"nombre": nombre, "tipo": tipo, "subtipo": subtipo, "id": cuenta_id}
            )
            flash('Cuenta actualizada exitosamente.', 'success')
    except Exception as e:
        print(f"Error en editar_cuenta: {e}")
        flash(f'Error al actualizar la cuenta: {e}', 'error')
    
    return redirect(url_for('admin.catalogo_cuentas'))