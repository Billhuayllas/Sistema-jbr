import json
import os
import uuid # For generating unique IDs

# Define the base directory correctly assuming models.py is inside modules/terceros/
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(MODULE_DIR)) 

DATA_FILE_TERCEROS = os.path.join(PROJECT_ROOT, 'terceros.json') 

def _ensure_terceros_data_file_exists():
    if not os.path.exists(DATA_FILE_TERCEROS):
        with open(DATA_FILE_TERCEROS, 'w', encoding='utf-8') as f:
            json.dump([], f)
    else:
        # Check if file is empty or invalid json
        try:
            with open(DATA_FILE_TERCEROS, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip(): # File is empty
                    # If empty, initialize with empty list
                    with open(DATA_FILE_TERCEROS, 'w', encoding='utf-8') as wf:
                        json.dump([], wf)
                    return 
                # Try to load it to check for validity if not empty
                # Need to re-open or seek(0) if read() was called - actually json.loads(content) is better
                json.loads(content) # This will raise JSONDecodeError if invalid
        except (json.JSONDecodeError, FileNotFoundError): 
             with open(DATA_FILE_TERCEROS, 'w', encoding='utf-8') as f:
                json.dump([], f)


def get_all_terceros():
    _ensure_terceros_data_file_exists()
    try:
        with open(DATA_FILE_TERCEROS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError: 
        return [] 

def add_tercero(data):
    terceros = get_all_terceros()
    new_tercero = {
        'id': str(uuid.uuid4()), 
        'nombre': data.get('nombre', '').strip(),
        'dni': data.get('dni', '').strip(),
        'direccion_principal': data.get('direccion_principal', '').strip(),
        'envio_departamento': data.get('envio_departamento', '').strip(),
        'envio_agencia': data.get('envio_agencia', '').strip(),
        'envio_notas': data.get('envio_notas', '').strip(),
        'telefono': data.get('telefono', '').strip(), 
        'email': data.get('email', '').strip()      
    }
    
    if not new_tercero['nombre']:
        raise ValueError("El campo 'nombre' es obligatorio para un tercero.")
    
    if new_tercero['dni']:
        if any(t.get('dni') == new_tercero['dni'] for t in terceros):
            raise ValueError(f"El DNI '{new_tercero['dni']}' ya existe para otro tercero.")

    terceros.append(new_tercero)
    with open(DATA_FILE_TERCEROS, 'w', encoding='utf-8') as f:
        json.dump(terceros, f, ensure_ascii=False, indent=4)
    return new_tercero

def get_tercero_by_id(tercero_id):
    terceros = get_all_terceros()
    for tercero in terceros:
        if tercero['id'] == tercero_id:
            return tercero
    return None

def update_tercero(tercero_id, data):
    terceros = get_all_terceros()
    tercero_to_update_idx = -1
    
    for i, t_loop in enumerate(terceros): # Renamed to avoid conflict with 'tercero' variable
        if t_loop['id'] == tercero_id:
            tercero_to_update_idx = i
            break
            
    if tercero_to_update_idx == -1:
        return None 

    tercero = terceros[tercero_to_update_idx] # Get the actual object to update

    updated_nombre = data.get('nombre', tercero['nombre']).strip()
    if not updated_nombre: 
        raise ValueError("El campo 'nombre' no puede estar vacío al actualizar.")
    tercero['nombre'] = updated_nombre
    
    updated_dni = data.get('dni', tercero.get('dni','')).strip() # Use .get for dni as it might not exist on old data
    if updated_dni and updated_dni != tercero.get('dni'): 
        if any(t.get('dni') == updated_dni and t.get('id') != tercero_id for t in terceros):
            raise ValueError(f"El DNI '{updated_dni}' ya existe para otro tercero.")
    tercero['dni'] = updated_dni
    
    tercero['direccion_principal'] = data.get('direccion_principal', tercero.get('direccion_principal','')).strip()
    tercero['envio_departamento'] = data.get('envio_departamento', tercero.get('envio_departamento','')).strip()
    tercero['envio_agencia'] = data.get('envio_agencia', tercero.get('envio_agencia','')).strip()
    tercero['envio_notas'] = data.get('envio_notas', tercero.get('envio_notas','')).strip()
    tercero['telefono'] = data.get('telefono', tercero.get('telefono', '')).strip() 
    tercero['email'] = data.get('email', tercero.get('email', '')).strip()         
    
    terceros[tercero_to_update_idx] = tercero 
    
    with open(DATA_FILE_TERCEROS, 'w', encoding='utf-8') as f:
        json.dump(terceros, f, ensure_ascii=False, indent=4)
    return tercero

def delete_tercero(tercero_id):
    terceros = get_all_terceros()
    original_len = len(terceros)
    terceros = [tercero for tercero in terceros if tercero['id'] != tercero_id]
    
    if len(terceros) < original_len:
        with open(DATA_FILE_TERCEROS, 'w', encoding='utf-8') as f:
            json.dump(terceros, f, ensure_ascii=False, indent=4)
        return True
    return False
```
