from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import get_all_entries, add_entry, get_entry_by_id, update_entry, delete_entry

accounts_receivable_bp = Blueprint(
    'accounts_receivable_bp', 
    __name__,
    template_folder='../../templates/accounts_receivable', # Path to templates
    static_folder='../../static' # Path to static, if any specific to this blueprint
)

@accounts_receivable_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        date = request.form.get('date')
        name = request.form.get('name')
        concept = request.form.get('concept')
        amount = request.form.get('amount')

        if not date or not name or not concept or not amount:
            flash('All fields are required.', 'error')
        else:
            try:
                amount = float(amount) # Basic validation for amount
                add_entry({'date': date, 'name': name, 'concept': concept, 'amount': amount})
                flash('Entry added successfully!', 'success')
            except ValueError:
                flash('Invalid amount. Please enter a number.', 'error')
        return redirect(url_for('accounts_receivable_bp.index'))

    entries = get_all_entries()
    return render_template('ar_index.html', entries=entries)

@accounts_receivable_bp.route('/edit/<string:entry_id>', methods=['GET', 'POST'])
def edit_entry_route(entry_id):
    entry = get_entry_by_id(entry_id)
    if not entry:
        flash('Entry not found.', 'error')
        return redirect(url_for('accounts_receivable_bp.index'))

    if request.method == 'POST':
        date = request.form.get('date')
        name = request.form.get('name')
        concept = request.form.get('concept')
        amount = request.form.get('amount')

        if not date or not name or not concept or not amount:
            flash('All fields are required.', 'error')
            return render_template('ar_edit_entry.html', entry=entry)
        
        try:
            amount = float(amount) # Basic validation for amount
            update_entry(entry_id, {'date': date, 'name': name, 'concept': concept, 'amount': amount})
            flash('Entry updated successfully!', 'success')
        except ValueError:
            flash('Invalid amount. Please enter a number.', 'error')
            return render_template('ar_edit_entry.html', entry=entry)
        
        return redirect(url_for('accounts_receivable_bp.index'))

    return render_template('ar_edit_entry.html', entry=entry)

@accounts_receivable_bp.route('/delete/<string:entry_id>', methods=['POST'])
def delete_entry_route(entry_id):
    if delete_entry(entry_id):
        flash('Entry deleted successfully!', 'success')
    else:
        flash('Error deleting entry or entry not found.', 'error')
    return redirect(url_for('accounts_receivable_bp.index'))
