import json
import uuid
import os
import datetime # For mark_as_paid

# Attempt to import carefully to avoid circularity
try:
    from modules.terceros.models import get_tercero_by_id as get_tercero_by_id_global
except ImportError:
    get_tercero_by_id_global = None
    print("WARNING: Could not import get_tercero_by_id_global in accounts_receivable.models. Tercero names will not be enriched.")

DATA_FILE = 'accounts_receivable.json'

def _ensure_data_file_exists():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    else:
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    with open(DATA_FILE, 'w', encoding='utf-8') as wf:
                        json.dump([], wf)
                    return
                json.loads(content) # Validate JSON
        except (json.JSONDecodeError, FileNotFoundError):
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)

def _normalize_entry(entry):
    # Ensure new fields (status, payment_date) exist with defaults
    entry.setdefault('status', 'pendiente')
    entry.setdefault('payment_date', None)

    # Map old field names ('concept', 'amount') to new ones ('descripcion', 'total')
    if 'concept' in entry and 'descripcion' not in entry:
        entry['descripcion'] = entry.pop('concept')
    entry.setdefault('descripcion', '')

    if 'amount' in entry and 'total' not in entry:
        entry['total'] = entry.pop('amount')
    entry.setdefault('total', 0.0)
    try: # Ensure total is float
        entry['total'] = float(entry['total'])
    except (ValueError, TypeError):
        entry['total'] = 0.0


    # Handle 'tercero_id' and old 'name' field.
    # If 'name' exists and 'tercero_id' does not, it's an old record.
    # The enrichment function will handle displaying this 'name'.
    if 'name' in entry and 'tercero_id' not in entry:
        # For internal consistency, we can set tercero_id to None if 'name' is present but 'tercero_id' isn't.
        # Or, we can decide that 'name' will be the primary key for display if tercero_id is missing.
        # For now, just ensure tercero_id exists as a key, even if None.
        entry.setdefault('tercero_id', None) 
    elif 'tercero_id' not in entry and 'name' not in entry:
        entry['tercero_id'] = None # Ensure key exists
    
    return entry

def _enrich_entry_with_tercero_name(entry):
    # Assumes entry is already normalized by _normalize_entry
    if entry.get('tercero_id') and get_tercero_by_id_global:
        tercero = get_tercero_by_id_global(entry['tercero_id'])
        entry['tercero_nombre'] = tercero['nombre'] if tercero else "Tercero Desconocido/Eliminado"
    elif entry.get('name'): # Backward compatibility: Use old 'name' if no 'tercero_id'
        entry['tercero_nombre'] = entry['name']
        # We might want to remove 'name' after using it for enrichment if 'tercero_id' is the primary way forward
        # entry.pop('name', None) 
    else:
        entry['tercero_nombre'] = "N/A (Sin Tercero)"
    return entry

def get_all_entries():
    _ensure_data_file_exists()
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            entries_raw = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        entries_raw = []
    
    processed_entries = []
    for entry_raw in entries_raw:
        normalized = _normalize_entry(entry_raw.copy()) # Use .copy() to avoid modifying original list in place during iteration
        enriched = _enrich_entry_with_tercero_name(normalized)
        processed_entries.append(enriched)
    return processed_entries

def add_entry(data): # Expects data['tercero_id'], data['date'], data['descripcion'], data['total']
    # The route will pass 'concept' as 'descripcion' and 'amount' as 'total'
    terceros_raw = get_all_entries_raw() # Get raw entries for saving

    new_entry_raw = {
        'id': str(uuid.uuid4()),
        'date': data.get('date'), 
        'tercero_id': data.get('tercero_id'), # Store tercero_id
        # 'name' field is no longer directly added; will be handled by enrichment or if old data exists
        'descripcion': data.get('descripcion'), 
        'total': 0.0,       
        'status': 'pendiente',
        'payment_date': None
    }
    try:
        new_entry_raw['total'] = float(data.get('total', 0.0))
    except (ValueError, TypeError):
        raise ValueError("El monto total debe ser un número válido.")


    if not all([new_entry_raw['date'], new_entry_raw['tercero_id'], new_entry_raw['descripcion']]):
        raise ValueError("Fecha, Tercero y Descripción son campos obligatorios.")
        
    terceros_raw.append(new_entry_raw)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(terceros_raw, f, indent=4, ensure_ascii=False)
    
    # Return the newly added entry, normalized and enriched
    return _enrich_entry_with_tercero_name(_normalize_entry(new_entry_raw.copy()))


def get_entry_by_id(entry_id):
    all_entries = get_all_entries() # This already returns normalized and enriched entries
    for entry in all_entries:
        if entry['id'] == entry_id:
            return entry 
    return None

def get_all_entries_raw(): # Helper to get non-enriched/non-normalized data for saving
    _ensure_data_file_exists()
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def update_entry(entry_id, data): # Expects data with 'tercero_id', 'date', 'descripcion', 'total'
    raw_entries = get_all_entries_raw()
    entry_updated = False
    updated_entry_for_return = None

    for i, entry_raw in enumerate(raw_entries):
        if entry_raw['id'] == entry_id:
            entry_raw['date'] = data.get('date', entry_raw['date']) 
            entry_raw['tercero_id'] = data.get('tercero_id', entry_raw.get('tercero_id'))
            entry_raw.pop('name', None) # Remove old 'name' field if present, as 'tercero_id' is primary

            entry_raw['descripcion'] = data.get('descripcion', entry_raw.get('descripcion'))
            try:
                entry_raw['total'] = float(data.get('total', entry_raw.get('total', 0.0)))
            except (ValueError, TypeError):
                raise ValueError("El monto total debe ser un número válido.")

            if not all([entry_raw['date'], entry_raw.get('tercero_id'), entry_raw['descripcion']]):
                raise ValueError("Fecha, Tercero y Descripción son campos obligatorios al actualizar.")

            # status and payment_date are preserved, handled by mark_as_paid
            entry_raw.setdefault('status', 'pendiente')
            entry_raw.setdefault('payment_date', None)

            raw_entries[i] = entry_raw
            entry_updated = True
            updated_entry_for_return = _enrich_entry_with_tercero_name(_normalize_entry(entry_raw.copy()))
            break

    if entry_updated:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(raw_entries, f, indent=4, ensure_ascii=False)
        return updated_entry_for_return
    return None


def delete_entry(entry_id):
    entries_raw = get_all_entries_raw()
    original_length = len(entries_raw)
    entries_raw = [entry for entry in entries_raw if entry['id'] != entry_id]
    if len(entries_raw) < original_length:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(entries_raw, f, indent=4, ensure_ascii=False)
        return True
    return False

def get_pending_entries():
    all_entries = get_all_entries() # Normalized and enriched
    pending_entries = [entry for entry in all_entries if entry.get('status') == 'pendiente']
    pending_entries.sort(key=lambda x: x.get('date', ''))
    return pending_entries

def get_paid_entries():
    all_entries = get_all_entries() # Normalized and enriched
    paid_entries = [entry for entry in all_entries if entry.get('status') == 'pagado']
    paid_entries.sort(key=lambda x: x.get('payment_date') or x.get('date', ''), reverse=True)
    return paid_entries

def mark_as_paid(entry_id):
    raw_entries = get_all_entries_raw()
    entry_found_and_updated = False
    updated_entry_for_return = None

    for i, entry_raw in enumerate(raw_entries):
        if entry_raw['id'] == entry_id:
            # Normalize to check current status correctly
            normalized_check_entry = _normalize_entry(entry_raw.copy())
            if normalized_check_entry.get('status') == 'pendiente':
                entry_raw['status'] = 'pagado'
                entry_raw['payment_date'] = datetime.date.today().isoformat()
                raw_entries[i] = entry_raw
                entry_found_and_updated = True
                updated_entry_for_return = _enrich_entry_with_tercero_name(_normalize_entry(entry_raw.copy()))
                break 
            else: # Already paid or other status
                return None # Indicate no change or invalid state

    if entry_found_and_updated:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(raw_entries, f, indent=4, ensure_ascii=False)
        return updated_entry_for_return
    return None # Entry not found or not updated

def calculate_sum(entries_list): # Expects a list of already processed (normalized/enriched) entries
    total_sum = 0
    for entry in entries_list:
        amount = entry.get('total', 0.0) # 'total' should be present and be a float due to normalization
        total_sum += amount
    return total_sum

```
