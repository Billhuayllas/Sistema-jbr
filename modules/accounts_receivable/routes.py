from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify # Added jsonify
from .models import (
    get_all_entries, add_entry, get_entry_by_id, update_entry, delete_entry, 
    get_pending_entries, get_paid_entries, model_mark_as_paid, calculate_sum
)
# Import from Terceros module
try:
    from modules.terceros.models import get_all_terceros as get_all_terceros_global
except ImportError:
    get_all_terceros_global = None # Fallback if Terceros module is not available
    current_app.logger.warning("Could not import get_all_terceros_global in accounts_receivable.routes. Tercero selection will be disabled.")

accounts_receivable_bp = Blueprint(
    'accounts_receivable_bp', 
    __name__,
    template_folder='../../templates/accounts_receivable', 
    static_folder='../../static'
)

@accounts_receivable_bp.route('/', methods=['GET']) # Changed to GET only for main view
def index():
    pending_entries = get_pending_entries()
    paid_entries = get_paid_entries()
    
    total_pending_amount = calculate_sum(pending_entries)
    total_paid_amount = calculate_sum(paid_entries)
    
    all_terceros = []
    if get_all_terceros_global:
        all_terceros = get_all_terceros_global()
    else:
        flash('Error: No se pudo cargar la lista de terceros. Funcionalidad limitada.', 'warning')
        
    return render_template(
        'ar_index.html', 
        pending_entries=pending_entries, 
        paid_entries=paid_entries,
        total_pending_amount=total_pending_amount,
        total_paid_amount=total_paid_amount,
        all_terceros=all_terceros # Pass terceros to template for dropdown
    )

# New route for adding entries, handling POST from the form in ar_index.html
@accounts_receivable_bp.route('/add', methods=['POST'])
def add_entry_route():
    # Form in ar_index.html will now submit 'tercero_id'
    
    tercero_id = request.form.get('tercero_id') 
    date = request.form.get('date')
    # The form in ar_index.html will now send 'tercero_id', 'date', 'descripcion', 'total'
    descripcion_from_form = request.form.get('descripcion') 
    total_str_from_form = request.form.get('total')    

    if not date or not tercero_id or not descripcion_from_form or not total_str_from_form:
        flash('Todos los campos (Fecha, Tercero, Descripción, Total) son obligatorios.', 'error')
    else:
        try:
            add_data = {
                'date': date, 
                'tercero_id': tercero_id, 
                'descripcion': descripcion_from_form, 
                'total': float(total_str_from_form)   
            }
            # add_entry will raise ValueError for model-level validation issues
            new_entry = add_entry(add_data) 
            flash('Entrada agregada exitosamente!', 'success')
        except ValueError as ve: # Catch validation errors from the model
            flash(str(ve), 'error')
        except Exception as e: # Catch other unexpected errors
            current_app.logger.error(f"Error adding AR entry: {e}", exc_info=True)
            flash('Error interno al agregar la entrada.', 'error')
            
    return redirect(url_for('accounts_receivable_bp.index'))

# New route for marking an entry as paid
@accounts_receivable_bp.route('/mark_paid/<string:entry_id>', methods=['POST'])
def mark_as_paid_route(entry_id):
    updated_entry = model_mark_as_paid(entry_id) # Use aliased model function
    if updated_entry:
        return jsonify({'success': True, 'message': 'Entrada marcada como pagada.'})
    else:
        # Check if entry exists to give a more specific message
        entry = get_entry_by_id(entry_id)
        if not entry:
            return jsonify({'success': False, 'message': 'Error: Entrada no encontrada.'}), 404
        elif entry.get('status') == 'pagado':
             return jsonify({'success': False, 'message': 'Esta entrada ya ha sido marcada como pagada.'}), 400
        else:
            return jsonify({'success': False, 'message': 'Error al marcar como pagada. Verifique el estado de la entrada.'}), 400


@accounts_receivable_bp.route('/edit/<string:entry_id>', methods=['GET', 'POST'])
def edit_entry_route(entry_id):
    entry = get_entry_by_id(entry_id)
    if not entry:
        flash('Entry not found.', 'error')
        return redirect(url_for('accounts_receivable_bp.index'))

    # GET request: Populate form for editing
    # The model's get_entry_by_id already normalizes and enriches fields.
    all_terceros_for_edit = []
    if get_all_terceros_global:
        all_terceros_for_edit = get_all_terceros_global()
    else:
        flash('Advertencia: No se pudo cargar la lista de terceros. La selección de tercero estará deshabilitada.', 'warning')

    if request.method == 'POST':
        # Form in ar_edit_entry.html will submit 'tercero_id', 'date', 'descripcion', 'total'
        tercero_id_form = request.form.get('tercero_id') 
        date_form = request.form.get('date')
        descripcion_form = request.form.get('descripcion') 
        total_str_form = request.form.get('total')

        if not date_form or not tercero_id_form or not descripcion_form or not total_str_form:
            flash('Todos los campos (Fecha, Tercero, Descripción, Total) son obligatorios.', 'error')
            # Re-render edit form with current data (which is 'entry') and all_terceros list
            return render_template('ar_edit_entry.html', entry=entry, all_terceros=all_terceros_for_edit)
        
        try:
            update_data = {
                'date': date_form, 
                'tercero_id': tercero_id_form, 
                'descripcion': descripcion_form, 
                'total': float(total_str_form)
            }
            # update_entry model function raises ValueError on failure
            updated = update_entry(entry_id, update_data) 
            flash('Entrada actualizada exitosamente!', 'success')
            return redirect(url_for('accounts_receivable_bp.index'))
        except ValueError as ve: # Catch validation errors from model
            flash(str(ve), 'error')
            # Re-render edit form, entry object should be the one currently being edited
            return render_template('ar_edit_entry.html', entry=entry, all_terceros=all_terceros_for_edit)
        except Exception as e: # Catch other unexpected errors
            current_app.logger.error(f"Error updating AR entry {entry_id}: {e}", exc_info=True)
            flash('Error interno al actualizar la entrada.', 'error')
            return render_template('ar_edit_entry.html', entry=entry, all_terceros=all_terceros_for_edit)

    # For GET request:
    # entry is already fetched and enriched by get_entry_by_id
    return render_template('ar_edit_entry.html', entry=entry, all_terceros=all_terceros_for_edit)

@accounts_receivable_bp.route('/delete/<string:entry_id>', methods=['POST'])
def delete_entry_route(entry_id):
    if delete_entry(entry_id):
        flash('Entry deleted successfully!', 'success')
    else:
        flash('Error deleting entry or entry not found.', 'error')
    return redirect(url_for('accounts_receivable_bp.index'))
