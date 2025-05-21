import json
import uuid
import os

DATA_FILE = 'accounts_receivable.json'

def _ensure_data_file_exists():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    else:
        # Check if file is empty or contains invalid JSON
        try:
            with open(DATA_FILE, 'r') as f:
                # Try to load the JSON data
                data = json.load(f)
                if not isinstance(data, list): # Ensure it's a list
                    raise ValueError("Data is not a list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            # If file is empty, not valid JSON, or doesn't exist (should be caught by os.path.exists but as a fallback)
            # Initialize with an empty list
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)


def get_all_entries():
    _ensure_data_file_exists()
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_entry(data):
    entries = get_all_entries()
    new_entry = {
        'id': str(uuid.uuid4()),
        'date': data.get('date'),
        'name': data.get('name'),
        'concept': data.get('concept'),
        'amount': data.get('amount')
    }
    entries.append(new_entry)
    with open(DATA_FILE, 'w') as f:
        json.dump(entries, f, indent=4)
    return new_entry

def get_entry_by_id(entry_id):
    entries = get_all_entries()
    for entry in entries:
        if entry['id'] == entry_id:
            return entry
    return None

def update_entry(entry_id, data):
    entries = get_all_entries()
    for i, entry in enumerate(entries):
        if entry['id'] == entry_id:
            entries[i]['date'] = data.get('date', entry['date'])
            entries[i]['name'] = data.get('name', entry['name'])
            entries[i]['concept'] = data.get('concept', entry['concept'])
            entries[i]['amount'] = data.get('amount', entry['amount'])
            with open(DATA_FILE, 'w') as f:
                json.dump(entries, f, indent=4)
            return entries[i]
    return None

def delete_entry(entry_id):
    entries = get_all_entries()
    original_length = len(entries)
    entries = [entry for entry in entries if entry['id'] != entry_id]
    if len(entries) < original_length:
        with open(DATA_FILE, 'w') as f:
            json.dump(entries, f, indent=4)
        return True
    return False
