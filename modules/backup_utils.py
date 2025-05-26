import json
import os
import datetime
import shutil # For optional file backup

# BASE_DIR should be the project root.
# If backup_utils.py is in 'modules/', then its parent is the project root.
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DATA_FILES_CONFIG = {
    # Paths assume JSON files are in subdirectories like 'product_catalog_data/product_catalog.json'
    # or directly in project root if that's the case.
    # The prompt suggests subdirectories, e.g., 'product_catalog/product_catalog.json'.
    # This implies the JSON files are NOT at the root, but in module-specific folders at the root.
    # Let's assume for now the JSON files are directly in the project root as per prior structure.
    # If they are indeed in module-specific subfolders, the paths here need changing.
    # The prompt's example for DATA_FILES_CONFIG has paths like:
    # 'product_catalog': os.path.join(BASE_DIR, 'product_catalog', 'product_catalog.json'),
    # This is different from the previous assumption that files like 'product_catalog.json' are at BASE_DIR.
    # I will use the paths as specified in THIS subtask's description.
    
    'product_catalog': os.path.join(BASE_DIR, 'product_catalog', 'product_catalog.json'),
    'product_series': os.path.join(BASE_DIR, 'product_catalog', 'product_series.json'),
    'product_categories': os.path.join(BASE_DIR, 'product_catalog', 'product_categories.json'),
    'product_marcas': os.path.join(BASE_DIR, 'product_catalog', 'product_marcas.json'),
    'product_juegos': os.path.join(BASE_DIR, 'product_catalog', 'product_juegos.json'),
    'accounts_receivable': os.path.join(BASE_DIR, 'accounts_receivable', 'accounts_receivable.json'),
    'cash_and_banks': os.path.join(BASE_DIR, 'cash_and_banks', 'cash_and_banks.json'),
}

# Ensure these subdirectories exist for the backup utility to function as expected if writing back.
# For reading, if files are not found, it will default to empty list.
# This requires that the actual JSON data files are stored in, e.g., /app/product_catalog/product_catalog.json

def _ensure_data_subdirs_exist():
    # This function is more relevant for restore, but good to be aware of path implications
    # For collect_all_data, it just means it might not find files if these dirs don't exist or paths are wrong.
    # Example: os.makedirs(os.path.join(BASE_DIR, 'product_catalog'), exist_ok=True)
    pass


def collect_all_data():
    _ensure_data_subdirs_exist() # Call this to be safe, though it does nothing yet
    all_data = {}
    for key, file_path in DATA_FILES_CONFIG.items():
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip(): 
                        all_data[key] = [] 
                    else:
                        all_data[key] = json.loads(content)
            else:
                print(f"Warning: Data file not found {file_path}. Defaulting to empty list for '{key}'.")
                all_data[key] = [] 
        except json.JSONDecodeError as je:
            print(f"JSON decode error reading {file_path}: {je}. File content: '{content[:100]}...'") # Log snippet
            all_data[key] = {'error': f'JSON decode error for {key}: {str(je)}', 'data': []}
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            all_data[key] = {'error': f'Error reading {key}: {str(e)}', 'data': []} 
    return all_data

def restore_all_data(backup_data_content):
    # backup_data_content is the value of the 'data' key from the backup file
    restored_files = []
    errors = []

    for key, data_to_restore in backup_data_content.items():
        file_path = DATA_FILES_CONFIG.get(key)
        if not file_path:
            errors.append(f"Configuration key '{key}' not found in DATA_FILES_CONFIG. Skipping.")
            continue

        # Optional: Backup existing file before overwriting
        # try:
        #     if os.path.exists(file_path):
        #         backup_file_path = file_path + ".bak." + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        #         shutil.copy2(file_path, backup_file_path) # Use shutil.copy2 to preserve metadata
        #         print(f"Backed up existing file {file_path} to {backup_file_path}")
        # except Exception as e:
        #     error_msg = f"Could not backup existing file {file_path}: {e}"
        #     print(error_msg)
        #     errors.append(error_msg)
            # Decide if you want to proceed or stop if backup fails. For now, proceeding.
            
        try:
            # Ensure directory exists
            target_dir = os.path.dirname(file_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                print(f"Created directory {target_dir}")
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_restore, f, ensure_ascii=False, indent=4)
            restored_files.append(file_path)
        except Exception as e:
            error_msg = f"Error restoring data to {file_path}: {e}"
            print(error_msg)
            errors.append(error_msg)
    
    if errors:
        return False, {"restored_count": len(restored_files), "files_attempted": len(backup_data_content), "errors": errors, "restored_files_list": restored_files}
    return True, {"restored_count": len(restored_files), "message": "Data restored successfully from backup."}

```
