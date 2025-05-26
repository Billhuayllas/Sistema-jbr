from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from .models import (
    add_tercero, get_all_terceros, get_tercero_by_id, 
    update_tercero, delete_tercero
) # Assuming models.py is in the same directory

# Adjusted template_folder to be relative to the blueprint's location (modules/terceros/)
# It needs to point to the global 'templates' directory, then 'terceros' subdirectory.
terceros_bp = Blueprint(
    'terceros_bp', 
    __name__, 
    template_folder='../../templates/terceros', 
    url_prefix='/terceros' # Added URL prefix
)

@terceros_bp.route('/')
def list_terceros_view():
    try:
        terceros = get_all_terceros()
        # Sort by name for consistent display, handle potential None for nombre
        terceros = sorted(terceros, key=lambda x: (x.get('nombre') or '').lower())
    except Exception as e:
        current_app.logger.error(f"Error fetching terceros: {e}")
        terceros = []
        flash('Error al cargar la lista de terceros.', 'danger') # Use flash for server-rendered page
    return render_template('terceros_list.html', terceros=terceros, title="Gestión de Terceros (Clientes)")

@terceros_bp.route('/add', methods=['POST'])
def add_tercero_route():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Solicitud no válida. Se esperaba JSON.'}), 400
        
    data = request.json
    try:
        if not data.get('nombre') or not data.get('nombre').strip(): # Ensure nombre is not just spaces
            return jsonify({'success': False, 'message': 'El nombre es obligatorio.'}), 400
        
        # Model's add_tercero already handles DNI uniqueness and raises ValueError
        new_tercero = add_tercero(data)
        if new_tercero is None: # Should not happen if ValueError is raised by model
             return jsonify({'success': False, 'message': 'Error al agregar tercero, posible DNI duplicado o datos inválidos.'}), 400
        return jsonify({'success': True, 'message': 'Tercero agregado exitosamente.', 'tercero': new_tercero})
    except ValueError as ve: 
        return jsonify({'success': False, 'message': str(ve)}), 400 # Return model's validation message
    except Exception as e:
        current_app.logger.error(f"Error adding tercero: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error interno al agregar el tercero.'}), 500


@terceros_bp.route('/details/<tercero_id>', methods=['GET'])
def get_tercero_details_route(tercero_id):
    tercero = get_tercero_by_id(tercero_id)
    if tercero:
        return jsonify(tercero)
    return jsonify({'success': False, 'message': 'Tercero no encontrado.'}), 404

@terceros_bp.route('/edit/<tercero_id>', methods=['POST'])
def edit_tercero_route(tercero_id):
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Solicitud no válida. Se esperaba JSON.'}), 400
        
    data = request.json
    try:
        if not data.get('nombre') or not data.get('nombre').strip():
            return jsonify({'success': False, 'message': 'El nombre es obligatorio.'}), 400
        
        # Model's update_tercero already handles DNI uniqueness and raises ValueError
        updated_tercero = update_tercero(tercero_id, data)
        if updated_tercero:
            return jsonify({'success': True, 'message': 'Tercero actualizado exitosamente.', 'tercero': updated_tercero})
        else: 
            # This 'else' might be hit if tercero_id not found by update_tercero, or model returns None for other reasons
            return jsonify({'success': False, 'message': 'Tercero no encontrado o error de validación en el modelo.'}), 404 
    except ValueError as ve: 
         return jsonify({'success': False, 'message': str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating tercero {tercero_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error interno al actualizar el tercero.'}), 500

@terceros_bp.route('/delete/<tercero_id>', methods=['POST'])
def delete_tercero_route(tercero_id):
    try:
        # TODO: Check if tercero is used in accounts_receivable before deleting.
        # This requires cross-module data access. For now, direct deletion.
        # from ..accounts_receivable.models import get_all_entries as get_ar_entries
        # ar_entries = get_ar_entries()
        # if any(entry.get('name') == tercero_nombre for entry in ar_entries): # Example check
        #     return jsonify({'success': False, 'message': 'Tercero en uso en Cuentas por Cobrar.'}), 409

        if delete_tercero(tercero_id):
            return jsonify({'success': True, 'message': 'Tercero eliminado exitosamente.'})
        return jsonify({'success': False, 'message': 'Tercero no encontrado.'}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting tercero {tercero_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'Error interno al eliminar el tercero.'}), 500

```
