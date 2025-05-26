from flask import Blueprint, jsonify, send_file, current_app
import json
import datetime
import io # For sending file from memory
import os # For potential path joining if needed, though backup_utils handles paths

from flask import Blueprint, jsonify, send_file, current_app, request, flash, render_template # Added render_template
import json
import datetime
import io 
import os 

from .backup_utils import collect_all_data, DATA_FILES_CONFIG, restore_all_data 

backup_bp = Blueprint('backup_bp', __name__, url_prefix='/backup')

@backup_bp.route('/') # Route for the main backup/restore page
def backup_general_view():
    return render_template('main/backup_general.html', title="Backup General del Sistema")

@backup_bp.route('/export_all_data')
def export_all_data_route():
    try:
        collected_data = collect_all_data()
        
        # Check if any data collection resulted in an error placeholder
        # This is a simple check; more sophisticated error handling might be needed
        # depending on how critical each data file is.
        for key, value in collected_data.items():
            if isinstance(value, dict) and 'error' in value:
                # Log the specific error for server-side awareness
                current_app.logger.error(f"Error collecting data for '{key}': {value['error']}")
                # Return a user-friendly error, perhaps listing which parts failed
                # For now, a general error if any part fails.
                # Or, could allow partial backup, with errors indicated in the backup file itself.
                # Let's proceed with backup but log errors. The collect_all_data includes error info.
                pass # Continue to create backup even if some parts have errors recorded within them.

        backup_content = {
            'version': '1.0.0', # Example version
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z', # ISO 8601 format
            'data': collected_data
        }
        
        # Create an in-memory file-like object for the JSON data
        json_string = json.dumps(backup_content, ensure_ascii=False, indent=4)
        
        # For send_file, it's better to use BytesIO
        mem_file = io.BytesIO()
        mem_file.write(json_string.encode('utf-8'))
        mem_file.seek(0) # Reset stream position to the beginning
        
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_sistema_completo_{timestamp_str}.json"
        
        return send_file(
            mem_file,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename 
        )
    except Exception as e:
        current_app.logger.error(f"Fatal error during backup export: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Error fatal al generar el backup: {str(e)}'}), 500

@backup_bp.route('/import_all_data', methods=['POST'])
def import_all_data_route():
    if 'backup_file' not in request.files:
        return jsonify({'success': False, 'message': 'No se encontró el archivo de backup.'}), 400
    
    file = request.files['backup_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo.'}), 400

    if file and file.filename.endswith('.json'):
        try:
            uploaded_content = json.load(file.stream) # Reads directly from the file stream

            # Validate basic structure
            if not isinstance(uploaded_content, dict) or \
               'version' not in uploaded_content or \
               'timestamp' not in uploaded_content or \
               'data' not in uploaded_content or \
               not isinstance(uploaded_content['data'], dict):
                return jsonify({'success': False, 'message': 'Formato de archivo de backup inválido. Faltan campos esenciales.'}), 400

            # Further validation: Check if keys in uploaded_content['data'] match DATA_FILES_CONFIG
            for key in uploaded_content['data'].keys():
                if key not in DATA_FILES_CONFIG:
                     return jsonify({'success': False, 'message': f"El archivo de backup contiene una clave de datos desconocida: '{key}'."}), 400
            
            # Ensure all expected keys are present in the backup (optional, depends on strictness)
            # for expected_key in DATA_FILES_CONFIG.keys():
            #    if expected_key not in uploaded_content['data']:
            #        return jsonify({'success': False, 'message': f"El archivo de backup no contiene datos para '{expected_key}'."}), 400

            success, result_info = restore_all_data(uploaded_content['data'])

            if success:
                return jsonify({'success': True, 'message': 'Datos restaurados exitosamente desde el backup.'})
            else:
                # Log detailed errors on server
                current_app.logger.error(f"Error during backup restore: {result_info.get('errors')}")
                # Return a summary of errors to the client
                error_summary = "; ".join(result_info.get('errors', ["Error desconocido durante la restauración."])[:3]) # Show first 3 errors
                return jsonify({
                    'success': False, 
                    'message': f'Ocurrieron errores al restaurar los datos: {error_summary}', 
                    'details': result_info.get('errors') # Full list of errors for client-side console if needed
                }), 500

        except json.JSONDecodeError:
            return jsonify({'success': False, 'message': 'Archivo de backup inválido: No es un JSON válido.'}), 400
        except Exception as e:
            current_app.logger.error(f"Error processing backup import: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': f'Error al procesar el archivo de backup: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'message': 'Formato de archivo no válido. Solo se permiten archivos .json.'}), 400

```
