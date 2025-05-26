from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify # Added jsonify
from .models import (
    add_transaction as model_add_transaction, # Aliased to avoid conflict if needed
    get_all_transactions, 
    get_transactions_by_date,
    get_transactions_by_account_type,
    get_transaction_by_id,
    update_transaction as model_update_transaction, # Aliased
    delete_transaction as model_delete_transaction, # Aliased
    calculate_saldo
    # calculate_totals and calculate_daily_totals are effectively replaced by calculate_saldo
)
import datetime # Import standard datetime

cash_and_banks_bp = Blueprint(
    'cash_and_banks_bp',
    __name__,
    template_folder='../../templates/cash_and_banks',
    static_folder='../../static'
)

@cash_and_banks_bp.route('/', methods=['GET']) # Main view, GET only
def index():
    today_date_iso = datetime.date.today().isoformat()

    # Filters for "Movimientos Actuales"
    ver_cuenta_filter = request.args.get('ver_cuenta_filter', 'Caja') # Default to 'Caja'
    ver_cuenta_banco_filter = request.args.get('ver_cuenta_banco_filter', None)
    
    # Adjust filter if "Todos" is selected for cuenta
    effective_cuenta_filter = None if ver_cuenta_filter == 'Todos' else ver_cuenta_filter
    
    current_transactions = get_transactions_by_account_type(
        cuenta_filter=effective_cuenta_filter, 
        banco_filter=ver_cuenta_banco_filter if effective_cuenta_filter == 'CuentaBancaria' else None
    )
    current_saldo = calculate_saldo(current_transactions) # Saldo for the currently displayed filtered list

    # Data for "Reporte Diario" section (defaults to today)
    report_date_str = request.args.get('report_date', today_date_iso) # Use today if no specific date requested
    report_transactions_for_date = get_transactions_by_date(report_date_str)
    
    report_neto_caja_today = calculate_saldo(report_transactions_for_date, {'cuenta': 'Caja'})
    report_neto_bancario_today = calculate_saldo(report_transactions_for_date, {'cuenta': 'CuentaBancaria'})
    report_neto_global_today = calculate_saldo(report_transactions_for_date) # All accounts for that day

    # Data for "Historial Completo" section (initial load, can be filtered by JS later)
    # For initial load, perhaps limit this or paginate if dataset is large. For now, load all.
    all_transactions_for_historial = get_all_transactions() 
    # Sort by date, most recent first for historial display
    all_transactions_for_historial.sort(key=lambda x: x.get('date', ''), reverse=True)


    selected_account_display_name = ver_cuenta_filter
    if ver_cuenta_filter == 'CuentaBancaria' and ver_cuenta_banco_filter:
        selected_account_display_name = f"Banco: {ver_cuenta_banco_filter}"
    elif ver_cuenta_filter == 'Todos':
        selected_account_display_name = "Todas las Cuentas"


    return render_template(
        'cb_index.html',
        today_date=today_date_iso, # For default value in date inputs
        current_transactions=current_transactions,
        current_saldo=current_saldo,
        selected_cuenta_filter=ver_cuenta_filter,
        selected_banco_filter=ver_cuenta_banco_filter,
        selected_account_display_name=selected_account_display_name,
        # Report data for the selected/default date (today)
        report_transactions_today=report_transactions_for_date, # For display in table
        report_neto_caja_today=report_neto_caja_today,
        report_neto_bancario_today=report_neto_bancario_today,
        report_neto_global_today=report_neto_global_today,
        report_date_str=report_date_str, # To show which date report is for
        # Historial data (initial full list)
        all_transactions_for_historial=all_transactions_for_historial
    )

# Route for adding new movements (transactions)
@cash_and_banks_bp.route('/add_movement', methods=['POST'])
def add_movement_route():
    form_data = request.form.to_dict()
    # Basic validation, model will handle more
    required_fields = ['date', 'descripcion', 'amount', 'tipo_movimiento', 'cuenta']
    if not all(form_data.get(field) for field in required_fields):
        flash('Todos los campos marcados con (*) son obligatorios.', 'error')
        return redirect(url_for('.index')) # Redirect back to main page

    if form_data.get('cuenta') == 'CuentaBancaria' and not form_data.get('banco'):
        flash('Por favor, seleccione un banco para movimientos de Cuenta Bancaria.', 'error')
        return redirect(url_for('.index'))

    # Amount is expected to be positive by model, tipo_movimiento handles direction
    try:
        form_data['amount'] = float(form_data['amount']) 
    except ValueError:
        flash('Monto inválido.', 'error')
        return redirect(url_for('.index'))

    new_tx = model_add_transaction(form_data)
    if new_tx:
        flash('Movimiento agregado exitosamente!', 'success')
    else:
        flash('Error al agregar el movimiento. Verifique los datos.', 'error')
    
    # Redirect to index, preserving current filters if possible (or reset)
    # For simplicity, redirecting without preserving filters for now.
    return redirect(url_for('.index'))


# AJAX Routes
@cash_and_banks_bp.route('/reporte_diario_data', methods=['GET'])
def get_daily_report_data_route():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Fecha no proporcionada.'}), 400
    try:
        # Validate date format if necessary
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400

    transactions_for_date = get_transactions_by_date(date_str)
    neto_caja = calculate_saldo(transactions_for_date, {'cuenta': 'Caja'})
    neto_bancario = calculate_saldo(transactions_for_date, {'cuenta': 'CuentaBancaria'})
    neto_global = calculate_saldo(transactions_for_date) # All accounts for that day

    return jsonify({
        'transactions': transactions_for_date,
        'neto_caja': neto_caja,
        'neto_bancario': neto_bancario,
        'neto_global': neto_global,
        'report_date_str': date_str # Echo back the date for clarity on UI
    })

@cash_and_banks_bp.route('/historial_data', methods=['GET'])
def get_historial_data_route():
    date_str = request.args.get('date')
    if date_str:
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            historical_txns = get_transactions_by_date(date_str)
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}), 400
    else:
        historical_txns = get_all_transactions()
    
    historical_txns.sort(key=lambda x: x.get('date', ''), reverse=True) # Ensure sorted
    return jsonify({'transactions': historical_txns})

@cash_and_banks_bp.route('/transaction_details/<string:transaction_id>', methods=['GET'])
def get_transaction_details_json_route(transaction_id):
    transaction = get_transaction_by_id(transaction_id)
    if transaction:
        return jsonify(transaction)
    return jsonify({'error': 'Transacción no encontrada.'}), 404

@cash_and_banks_bp.route('/edit_transaction/<string:transaction_id>', methods=['POST'])
def edit_transaction_route(transaction_id):
    # Assuming data is sent as JSON from client for AJAX edit
    # If using standard form post, use request.form.to_dict()
    data = request.form.to_dict() # From addMovementForm populated by JS
    
    # Basic validation (similar to add_movement_route)
    required_fields = ['date', 'descripcion', 'amount', 'tipo_movimiento', 'cuenta']
    if not all(data.get(field) for field in required_fields):
        return jsonify(success=False, message='Campos obligatorios faltantes.'), 400
    if data.get('cuenta') == 'CuentaBancaria' and not data.get('banco'):
         return jsonify(success=False, message='Banco es obligatorio para Cuenta Bancaria.'), 400

    try:
        data['amount'] = float(data['amount'])
    except ValueError:
        return jsonify(success=False, message='Monto inválido.'), 400

    updated_tx = model_update_transaction(transaction_id, data)
    if updated_tx:
        return jsonify(success=True, message='Movimiento actualizado exitosamente!', transaction=updated_tx)
    else:
        return jsonify(success=False, message='Error al actualizar el movimiento o no se encontró.'), 404

@cash_and_banks_bp.route('/delete_transaction/<string:transaction_id>', methods=['POST'])
def delete_transaction_route(transaction_id):
    if model_delete_transaction(transaction_id):
        return jsonify(success=True, message='Movimiento eliminado exitosamente!')
    else:
        return jsonify(success=False, message='Error al eliminar el movimiento o no se encontró.'), 404

@cash_and_banks_bp.route('/corte_de_caja', methods=['POST'])
def corte_de_caja_route():
    # Placeholder for now
    # Real implementation:
    # 1. Calculate current saldo for 'Caja' (and potentially others).
    # 2. Archive/mark transactions up to this point as "closed" or part of this "corte".
    # 3. Create a new "saldo inicial" transaction for 'Caja' for the next period.
    # This is complex and depends on specific accounting rules.
    return jsonify({'success': False, 'message': 'Funcionalidad de Corte de Caja no implementada completamente.'})


# Old /daily_report/ and /corte_de_caja/ GET routes can be removed if new AJAX routes cover their display needs
# or kept if they serve a different full-page view purpose.
# For now, let's comment them out to avoid confusion with new AJAX routes.

# @cash_and_banks_bp.route('/daily_report/', methods=['GET'])
# def daily_report():
#     selected_date_str = request.args.get('date')
#     transactions_for_date = []
#     daily_totals_data = None

#     if selected_date_str:
#         try:
#             datetime.datetime.strptime(selected_date_str, '%Y-%m-%d') 
#             transactions_for_date = get_transactions_by_date(selected_date_str)
#             if not transactions_for_date:
#                 flash(f'No transactions found for {selected_date_str}.', 'info')
#         except ValueError:
#             flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
#             selected_date_str = None 

#     return render_template('cb_daily_report.html',
#                            transactions=transactions_for_date,
#                            selected_date=selected_date_str)


# @cash_and_banks_bp.route('/corte_de_caja/', methods=['GET'])
# def corte_de_caja():
#     # This old route displayed overall totals and today's totals.
#     # The main index route now shows current saldo based on filters.
#     # The AJAX /reporte_diario_data provides daily totals.
#     # This specific GET view might be redundant or need re-purposing.
    
#     # Example of what it might have done, now covered elsewhere:
#     # overall_totals = calculate_saldo(get_all_transactions()) # This is a global saldo
#     # today_str = datetime.date.today().isoformat()
#     # daily_txns = get_transactions_by_date(today_str)
#     # daily_totals_data = {
#     #     'today_cash': calculate_saldo(daily_txns, {'cuenta':'Caja'}),
#     #     'today_bank': calculate_saldo(daily_txns, {'cuenta':'CuentaBancaria'}),
#     #     'today_grand_total': calculate_saldo(daily_txns)
#     # }
    
#     # return render_template('cb_corte_de_caja.html',
#     #                        overall_totals={'grand_total': overall_totals}, # Simplified
#     #                        daily_totals=daily_totals_data,
#     #                        today_date_str=today_str)
+    flash("La vista de 'Corte de Caja' individual ha sido integrada en la página principal de Rendición de Caja.", "info")
+    return redirect(url_for('.index'))


@cash_and_banks_bp.route('/daily_report/', methods=['GET'])
def daily_report():
    selected_date_str = request.args.get('date')
    transactions_for_date = []
    daily_totals_data = None

    if selected_date_str:
        try:
            # Validate date format if necessary, though models.py doesn't strictly enforce
            datetime.strptime(selected_date_str, '%Y-%m-%d') # Basic validation
            transactions_for_date = get_transactions_by_date(selected_date_str)
            if not transactions_for_date:
                flash(f'No transactions found for {selected_date_str}.', 'info')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            selected_date_str = None # Reset to show the form again

    return render_template('cb_daily_report.html',
                           transactions=transactions_for_date,
                           selected_date=selected_date_str)


@cash_and_banks_bp.route('/corte_de_caja/', methods=['GET'])
def corte_de_caja():
    overall_totals = calculate_totals()
    
    # For "Today's" totals
    today_str = datetime.now().strftime('%Y-%m-%d')
    daily_totals_data = calculate_daily_totals(today_str)
    
    return render_template('cb_corte_de_caja.html',
                           overall_totals=overall_totals,
                           daily_totals=daily_totals_data,
                           today_date_str=today_str)
