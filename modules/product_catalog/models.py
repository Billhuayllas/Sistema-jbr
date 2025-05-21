import json
import uuid
import os
from werkzeug.utils import secure_filename

DATA_FILE = 'product_catalog.json'
IMAGE_UPLOAD_FOLDER = 'static/uploads/products/' # Relative to the app's static folder

PRODUCT_SERIES = [
    "aceites", "anillos", "sincronizadores", "sincronizadores deslizantes",
    "propulsores", "canastillas", "rodajes", "cajas", "otros"
]

def _ensure_data_file_exists():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    else:
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Data is not a list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)

def _ensure_image_upload_folder_exists():
    # Create the full path by joining with the 'static' directory,
    # as IMAGE_UPLOAD_FOLDER is relative to 'static'
    # However, Flask handles 'static' implicitly.
    # The models.py is in modules/product_catalog.
    # So IMAGE_UPLOAD_FOLDER needs to be relative to the app root.
    # For direct os.makedirs, we need to construct the path from app root.
    # Assuming app.py is at the root:
    
    # Correct path from project root:
    # For Flask, 'static/uploads/products' is typically accessed as url_for('static', filename='uploads/products/...')
    # The IMAGE_UPLOAD_FOLDER should represent the actual file system path for saving.
    # If app.py is at root, and this file is in modules/product_catalog/models.py
    # Then the path from this file to the static folder is '../../static/uploads/products/'
    
    # Let's assume IMAGE_UPLOAD_FOLDER is defined relative to the application's root directory
    # For saving files, we need to make sure the path is correct.
    # If Flask's app.config['UPLOAD_FOLDER'] is set to os.path.join(app.root_path, IMAGE_UPLOAD_FOLDER)
    # then we can just use that. Here, we are in models.py.
    
    # For simplicity, let's assume the UPLOAD_FOLDER is correctly configured in app.py
    # and this function is more about ensuring the directory exists
    # using the path as defined.
    
    # The path needs to be accessible from where app.py runs.
    # So, 'static/uploads/products' as a top-level dir in the project.
    
    # Let's adjust IMAGE_UPLOAD_FOLDER to be an absolute path or ensure it's handled correctly by app.py
    # For now, assume 'static/uploads/products' is relative to the project root.
    
    # This path will be relative to where the script is run from (usually the project root)
    # or where app.py is.
    if not os.path.exists(IMAGE_UPLOAD_FOLDER):
        os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)


def get_all_products():
    _ensure_data_file_exists()
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_product(data, image_file):
    _ensure_image_upload_folder_exists()
    products = get_all_products()
    
    filename = None
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        # The UPLOAD_FOLDER config in Flask app should point to the correct absolute path
        # For now, we construct it assuming IMAGE_UPLOAD_FOLDER is relative to project root
        image_save_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
        image_file.save(image_save_path)

    new_product = {
        'id': str(uuid.uuid4()),
        'product_code': data.get('product_code'),
        'name': data.get('name'),
        'price_fox': data.get('price_fox'),
        'cost': data.get('cost'),
        'price_wholesale': data.get('price_wholesale'),
        'price_unit': data.get('price_unit'),
        'series': data.get('series'),
        'image_filename': filename
    }
    products.append(new_product)
    with open(DATA_FILE, 'w') as f:
        json.dump(products, f, indent=4)
    return new_product

def get_product_by_id(product_id):
    products = get_all_products()
    for product in products:
        if product['id'] == product_id:
            return product
    return None

def update_product(product_id, data, image_file=None):
    _ensure_image_upload_folder_exists()
    products = get_all_products()
    product_found = False
    for i, product in enumerate(products):
        if product['id'] == product_id:
            # Handle image update
            if image_file and image_file.filename:
                # Delete old image if it exists and is different
                if product.get('image_filename'):
                    old_image_path = os.path.join(IMAGE_UPLOAD_FOLDER, product['image_filename'])
                    if os.path.exists(old_image_path):
                        # Only delete if the new filename is different, or if we always replace
                        # For simplicity, let's assume we might be overwriting with the same name
                        # or a new name. If it's a new name, the old one should be deleted.
                        # If it's the same name, werkzeug.secure_filename will handle it.
                         pass # Decide on deletion strategy later if needed.

                filename = secure_filename(image_file.filename)
                image_save_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
                image_file.save(image_save_path)
                products[i]['image_filename'] = filename
            
            # Update other fields
            products[i]['product_code'] = data.get('product_code', product['product_code'])
            products[i]['name'] = data.get('name', product['name'])
            products[i]['price_fox'] = data.get('price_fox', product['price_fox'])
            products[i]['cost'] = data.get('cost', product['cost'])
            products[i]['price_wholesale'] = data.get('price_wholesale', product['price_wholesale'])
            products[i]['price_unit'] = data.get('price_unit', product['price_unit'])
            products[i]['series'] = data.get('series', product['series'])
            product_found = True
            break
            
    if product_found:
        with open(DATA_FILE, 'w') as f:
            json.dump(products, f, indent=4)
        return products[i] if product_found else None # Should be product_found here
    return None


def delete_product(product_id):
    products = get_all_products()
    product_to_delete = None
    for product in products:
        if product['id'] == product_id:
            product_to_delete = product
            break

    if not product_to_delete:
        return False

    # Delete image file if it exists
    if product_to_delete.get('image_filename'):
        image_path = os.path.join(IMAGE_UPLOAD_FOLDER, product_to_delete['image_filename'])
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError as e:
                print(f"Error deleting image {image_path}: {e}") # Log this instead of print

    new_products = [p for p in products if p['id'] != product_id]
    if len(new_products) < len(products):
        with open(DATA_FILE, 'w') as f:
            json.dump(new_products, f, indent=4)
        return True
    return False

def get_products_by_series(series_name):
    products = get_all_products()
    if not series_name: # If series_name is empty or None, return all products
        return products
    return [product for product in products if product.get('series') == series_name]
