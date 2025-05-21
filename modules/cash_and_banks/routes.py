from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import (
    get_all_transactions, add_transaction, get_transactions_by_date,
    calculate_totals, calculate_daily_totals
)
from datetime import datetime

cash_and_banks_bp = Blueprint(
    'cash_and_banks_bp',
    __name__,
    template_folder='../../templates/cash_and_banks',
    static_folder='../../static'
)

@cash_and_banks_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        date = request.form.get('date')
        concept = request.form.get('concept')
        amount = request.form.get('amount')
        transaction_type = request.form.get('type')

        if not date or not concept or not amount or not transaction_type:
            flash('All fields are required.', 'error')
        else:
            try:
                amount_float = float(amount)
                add_transaction({
                    'date': date,
                    'concept': concept,
                    'amount': amount_float,
                    'type': transaction_type
                })
                flash('Transaction added successfully!', 'success')
            except ValueError:
                flash('Invalid amount. Please enter a number.', 'error')
        return redirect(url_for('cash_and_banks_bp.index'))

    transactions = get_all_transactions()
    totals = calculate_totals()
    return render_template('cb_index.html', transactions=transactions, totals=totals)

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
