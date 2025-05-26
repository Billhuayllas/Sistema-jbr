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

# Placeholder for series data - in a real app, this would come from a database or another JSON file
def get_all_series_data():
    """Returns a dictionary of series data including names and colors."""
    # Example: {'S001': {'name': 'Aceites', 'color': '#FFD700'}, ...}
    # For now, let's map from PRODUCT_SERIES
    series_map = {}
    colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c', '#d35400', '#7f8c8d']
    for i, series_code_or_name in enumerate(PRODUCT_SERIES):
        # Assuming PRODUCT_SERIES contains codes/IDs. If names, adjust accordingly.
        # For this example, let's treat items in PRODUCT_SERIES as the 'name' and generate a code.
        code = f"SER{i+1:03}" # e.g., SER001
        series_map[code] = {
            'name': series_code_or_name.capitalize(), # Use the name from PRODUCT_SERIES
            'code': code, # Store the generated code
            'color': colors[i % len(colors)]
        }
    # This function should return a structure that's easy to use in the template
    # e.g., a dictionary keyed by series code.
    # Let's also return a list version for dropdowns
    # This function will now source its data from get_all_series()
    all_series_objects = get_all_series() # List of {'id':uuid, 'codigo':'SER001', 'nombre':'Aceites', 'color':'#...'}
    
    series_map = {}
    series_list_for_dropdown = []

    for serie_obj in all_series_objects:
        # The 'code' key for the map and dropdown should be the 'codigo' field from the serie object
        series_map[serie_obj['codigo']] = {
            'name': serie_obj['nombre'],
            'color': serie_obj.get('color', '#7f8c8d'), # Default color if not set
            'code': serie_obj['codigo'] # Include code itself for consistency if needed
        }
        series_list_for_dropdown.append({
            'code': serie_obj['codigo'], # This is the value for <option value="">
            'name': serie_obj['nombre']  # This is the text displayed in dropdown
        })
    return series_map, series_list_for_dropdown


# --- Series Data Management ---
DATA_FILE_SERIES = 'product_series.json'

def _ensure_series_data_file_exists():
    if not os.path.exists(DATA_FILE_SERIES):
        # Initialize with some defaults from PRODUCT_SERIES if it's still around, or empty list
        # For now, initialize empty, PRODUCT_SERIES constant is deprecated.
        with open(DATA_FILE_SERIES, 'w') as f:
            json.dump([], f)
    else:
        try:
            with open(DATA_FILE_SERIES, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list): raise ValueError("Series data is not a list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(DATA_FILE_SERIES, 'w') as f: json.dump([], f)

def get_all_series():
    _ensure_series_data_file_exists()
    try:
        with open(DATA_FILE_SERIES, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_serie(data): # data = {'codigo': 'S001', 'nombre': 'Aceites', 'color': '#FF0000'}
    series_list = get_all_series()
    # Check for unique codigo
    if any(s['codigo'].lower() == data.get('codigo', '').lower() for s in series_list):
        # Consider raising an error or returning a specific value indicating failure
        print(f"Error: Serie codigo {data.get('codigo')} already exists.") # Should be logged
        return None # Or raise ValueError("Series code must be unique")

    new_serie = {
        'id': str(uuid.uuid4()),
        'codigo': data.get('codigo', '').strip().upper(), # Standardize codigo
        'nombre': data.get('nombre', '').strip(),
        'color': data.get('color', '#7f8c8d') # Default color
    }
    if not new_serie['codigo'] or not new_serie['nombre']: # Basic validation
        print("Error: Codigo and Nombre are required for a serie.")
        return None

    series_list.append(new_serie)
    with open(DATA_FILE_SERIES, 'w') as f:
        json.dump(series_list, f, indent=4)
    return new_serie

def get_serie_by_id(serie_id):
    series_list = get_all_series()
    for serie in series_list:
        if serie['id'] == serie_id:
            return serie
    return None

def update_serie(serie_id, data): # data = {'nombre': 'Nuevos Aceites', 'color': '#00FF00'} - codigo not editable
    series_list = get_all_series()
    for i, serie in enumerate(series_list):
        if serie['id'] == serie_id:
            # Codigo is not updatable to maintain integrity with products using it.
            # If it needs to be updatable, product series references must also be updated.
            series_list[i]['nombre'] = data.get('nombre', serie['nombre']).strip()
            series_list[i]['color'] = data.get('color', serie.get('color', '#7f8c8d'))
            
            if not series_list[i]['nombre']: # Basic validation
                 print("Error: Nombre cannot be empty for a serie.")
                 return None # Or old object if partial update is not desired on error

            with open(DATA_FILE_SERIES, 'w') as f:
                json.dump(series_list, f, indent=4)
            return series_list[i]
    return None

def delete_serie(serie_id):
    series_list = get_all_series()
    original_length = len(series_list)
    series_list = [s for s in series_list if s['id'] != serie_id]
    if len(series_list) < original_length:
        # TODO: Check if this series is used by any product. If so, prevent deletion or handle orphaned data.
        # For now, direct deletion.
        with open(DATA_FILE_SERIES, 'w') as f:
            json.dump(series_list, f, indent=4)
        return True
    return False

# --- Marcas (Brands) Data Management ---
DATA_FILE_MARCAS = 'product_marcas.json'

def _ensure_marcas_data_file_exists():
    if not os.path.exists(DATA_FILE_MARCAS):
        # Initialize with some defaults if needed, or empty list
        # Defaults from previous get_all_brands_data were more like product instances,
        # here we just store brand names and assign codes/IDs.
        initial_marcas = [
            {'id': str(uuid.uuid4()), 'nombre': 'Marca A (Fox)'},
            {'id': str(uuid.uuid4()), 'nombre': 'Marca B (Global Parts)'},
            {'id': str(uuid.uuid4()), 'nombre': 'Toyota'},
            {'id': str(uuid.uuid4()), 'nombre': 'Chevrolet'},
            {'id': str(uuid.uuid4()), 'nombre': 'Nissan'},
            # Add more if desired from the old hardcoded list
        ]
        with open(DATA_FILE_MARCAS, 'w') as f: json.dump(initial_marcas, f, indent=4)
    else:
        try:
            with open(DATA_FILE_MARCAS, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list): raise ValueError("Marcas data is not a list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(DATA_FILE_MARCAS, 'w') as f: json.dump([], f)

def get_all_marcas():
    _ensure_marcas_data_file_exists()
    try:
        with open(DATA_FILE_MARCAS, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_marca(data): # data = {'nombre': 'Nueva Marca'}
    marcas_list = get_all_marcas()
    nombre = data.get('nombre', '').strip()
    if not nombre:
        print("Error: Nombre is required for a marca.")
        return None
    if any(m['nombre'].lower() == nombre.lower() for m in marcas_list):
        print(f"Error: Marca nombre '{nombre}' already exists.")
        return None # Or raise ValueError

    new_marca = {
        'id': str(uuid.uuid4()),
        'nombre': nombre
    }
    marcas_list.append(new_marca)
    with open(DATA_FILE_MARCAS, 'w') as f:
        json.dump(marcas_list, f, indent=4)
    return new_marca

def get_marca_by_id(marca_id):
    marcas_list = get_all_marcas()
    for marca in marcas_list:
        if marca['id'] == marca_id:
            return marca
    return None

def update_marca(marca_id, data): # data = {'nombre': 'Nombre Actualizado'}
    marcas_list = get_all_marcas()
    nombre_nuevo = data.get('nombre', '').strip()
    if not nombre_nuevo:
        print("Error: Nombre cannot be empty for a marca.")
        return None

    # Check for uniqueness if name is changed
    # Find the current marca first to compare its current name
    current_marca_index = -1
    for i, m in enumerate(marcas_list):
        if m['id'] == marca_id:
            current_marca_index = i
            break
    
    if current_marca_index == -1: return None # Not found

    # If name is actually changing, check for uniqueness against OTHER marcas
    if marcas_list[current_marca_index]['nombre'].lower() != nombre_nuevo.lower():
        if any(m['nombre'].lower() == nombre_nuevo.lower() and m['id'] != marca_id for m in marcas_list):
            print(f"Error: Marca nombre '{nombre_nuevo}' already exists.")
            return None # Or raise ValueError

    marcas_list[current_marca_index]['nombre'] = nombre_nuevo
    with open(DATA_FILE_MARCAS, 'w') as f:
        json.dump(marcas_list, f, indent=4)
    return marcas_list[current_marca_index]

def delete_marca(marca_id):
    marcas_list = get_all_marcas()
    original_length = len(marcas_list)
    marcas_list = [m for m in marcas_list if m['id'] != marca_id]
    if len(marcas_list) < original_length:
        # TODO: Check if this marca is used by any product.
        with open(DATA_FILE_MARCAS, 'w') as f:
            json.dump(marcas_list, f, indent=4)
        return True
    return False


# Update get_all_brands_data to use the new model functions
def get_all_brands_data():
    """Returns a list of brand data suitable for dropdowns."""
    all_marcas_objects = get_all_marcas() # List of {'id':uuid, 'nombre':'Marca A'}
    # The product form expects a list of dicts with 'code' and 'name'.
    # For Marcas, the 'id' can serve as 'code' for the value of <option>
    brands_list_for_dropdown = []
    for marca_obj in all_marcas_objects:
        brands_list_for_dropdown.append({
            'code': marca_obj['id'], # Use ID as the 'code' for selection value
            'name': marca_obj['nombre']
        })
    return brands_list_for_dropdown

# --- Categories Data Management ---
DATA_FILE_CATEGORIES = 'product_categories.json'

def _ensure_categories_data_file_exists():
    if not os.path.exists(DATA_FILE_CATEGORIES):
        initial_categories = [
            {'id': str(uuid.uuid4()), 'nombre': 'Motor'},
            {'id': str(uuid.uuid4()), 'nombre': 'Suspensión y Dirección'},
            {'id': str(uuid.uuid4()), 'nombre': 'Frenos'},
            # Add more from old hardcoded list if desired
        ]
        with open(DATA_FILE_CATEGORIES, 'w') as f: json.dump(initial_categories, f, indent=4)
    else:
        try:
            with open(DATA_FILE_CATEGORIES, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list): raise ValueError("Categories data is not a list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(DATA_FILE_CATEGORIES, 'w') as f: json.dump([], f)

def get_all_categories():
    _ensure_categories_data_file_exists()
    try:
        with open(DATA_FILE_CATEGORIES, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_category(data): # data = {'nombre': 'Nueva Categoría'}
    categories_list = get_all_categories()
    nombre = data.get('nombre', '').strip()
    if not nombre:
        print("Error: Nombre is required for a category.")
        return None
    if any(c['nombre'].lower() == nombre.lower() for c in categories_list):
        print(f"Error: Category nombre '{nombre}' already exists.")
        return None

    new_category = {
        'id': str(uuid.uuid4()),
        'nombre': nombre
    }
    categories_list.append(new_category)
    with open(DATA_FILE_CATEGORIES, 'w') as f:
        json.dump(categories_list, f, indent=4)
    return new_category

def get_category_by_id(category_id):
    categories_list = get_all_categories()
    for category in categories_list:
        if category['id'] == category_id:
            return category
    return None

def update_category(category_id, data): # data = {'nombre': 'Nombre Actualizado'}
    categories_list = get_all_categories()
    nombre_nuevo = data.get('nombre', '').strip()
    if not nombre_nuevo:
        print("Error: Nombre cannot be empty for a category.")
        return None

    current_category_index = -1
    for i, c in enumerate(categories_list):
        if c['id'] == category_id:
            current_category_index = i
            break
    
    if current_category_index == -1: return None

    if categories_list[current_category_index]['nombre'].lower() != nombre_nuevo.lower():
        if any(c['nombre'].lower() == nombre_nuevo.lower() and c['id'] != category_id for c in categories_list):
            print(f"Error: Category nombre '{nombre_nuevo}' already exists.")
            return None

    categories_list[current_category_index]['nombre'] = nombre_nuevo
    with open(DATA_FILE_CATEGORIES, 'w') as f:
        json.dump(categories_list, f, indent=4)
    return categories_list[current_category_index]

def delete_category(category_id):
    categories_list = get_all_categories()
    original_length = len(categories_list)
    categories_list = [c for c in categories_list if c['id'] != category_id]
    if len(categories_list) < original_length:
        # TODO: Check if this category is used by any product.
        with open(DATA_FILE_CATEGORIES, 'w') as f:
            json.dump(categories_list, f, indent=4)
        return True
    return False

# Update get_all_categories_data to use the new model functions
def get_all_categories_data():
    """Returns a list of category data suitable for dropdowns."""
    all_categories_objects = get_all_categories()
    # Product form expects list of dicts with 'code' and 'name'
    # Category 'id' can serve as 'code'
    categories_list_for_dropdown = []
    for cat_obj in all_categories_objects:
        categories_list_for_dropdown.append({
            'code': cat_obj['id'], # Use ID as 'code'
            'name': cat_obj['nombre']
        })
    return categories_list_for_dropdown

# The old placeholder get_all_categories_data() is now removed as the new one above sources from JSON.
        {'code': 'B007', 'name': 'Kia'},
        {'code': 'B008', 'name': 'Mazda'},
        {'code': 'B009', 'name': 'Mitsubishi'},
        {'code': 'B010', 'name': 'Volkswagen'},
        {'code': 'B011', 'name': 'Ford'},
        {'code': 'B012', 'name': 'Honda'},
        {'code': 'B013', 'name': 'Suzuki'},
        {'code': 'B014', 'name': 'Peugeot'},
        {'code': 'B015', 'name': 'Renault'},
        {'code': 'B016', 'name': 'Mercedes-Benz'},
        {'code': 'B017', 'name': 'BMW'},
        {'code': 'B018', 'name': 'Audi'},
        {'code': 'B019', 'name': 'Fiat'},
        {'code': 'B020', 'name': 'Otra Genérica'},
    ]

# Placeholder for category data
def get_all_categories_data():
    """Returns a list of category data."""
    # Example: [{'code': 'C001', 'name': 'Electrónica'}, ...]
    # This would typically come from a DB or JSON file.
    return [
        {'code': 'C001', 'name': 'Motor'},
        {'code': 'C002', 'name': 'Suspensión y Dirección'},
        {'code': 'C003', 'name': 'Frenos'},
        {'code': 'C004', 'name': 'Transmisión y Embrague'},
        {'code': 'C005', 'name': 'Sistema Eléctrico'},
        {'code': 'C006', 'name': 'Refrigeración y Calefacción'},
        {'code': 'C007', 'name': 'Carrocería y Cristales'},
        {'code': 'C008', 'name': 'Interior'},
        {'code': 'C009', 'name': 'Accesorios y Herramientas'},
        {'code': 'C010', 'name': 'Lubricantes y Fluidos'},
        {'code': 'C011', 'name': 'Llantas y Neumáticos'},
        {'code': 'C012', 'name': 'Iluminación'},
    ]

DATA_FILE_JUEGOS = 'product_juegos.json'

def _ensure_juegos_data_file_exists():
    if not os.path.exists(DATA_FILE_JUEGOS):
        with open(DATA_FILE_JUEGOS, 'w') as f:
            json.dump([], f)
    else:
        try:
            with open(DATA_FILE_JUEGOS, 'r') as f:
                data = json.load(f)
                if not isinstance(data, list): # Ensure it's a list
                    raise ValueError("Juegos data is not a list")
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(DATA_FILE_JUEGOS, 'w') as f:
                json.dump([], f)

def get_all_juegos():
    _ensure_juegos_data_file_exists()
    try:
        with open(DATA_FILE_JUEGOS, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_juego(data):
    juegos = get_all_juegos()
    new_juego = {
        'id': str(uuid.uuid4()),
        'codigo': data.get('codigo'),
        'nombre': data.get('nombre'),
        'aplicaciones': data.get('aplicaciones', []), # List of {'vehiculo': '', 'marcaVehiculo': ''}
        'componentes': data.get('componentes', []) # List of {'productoId': id, 'cantidad': qty}
    }
    juegos.append(new_juego)
    with open(DATA_FILE_JUEGOS, 'w') as f:
        json.dump(juegos, f, indent=4)
    return new_juego

def get_juego_by_id(juego_id):
    juegos = get_all_juegos()
    for juego in juegos:
        if juego['id'] == juego_id:
            # Ensure all fields are present, especially new list fields
            juego.setdefault('aplicaciones', [])
            juego.setdefault('componentes', [])
            return juego
    return None

def update_juego(juego_id, data):
    juegos = get_all_juegos()
    for i, juego in enumerate(juegos):
        if juego['id'] == juego_id:
            juegos[i]['codigo'] = data.get('codigo', juego['codigo'])
            juegos[i]['nombre'] = data.get('nombre', juego['nombre'])
            # For aplicaciones and componentes, replace if provided, else keep old
            if 'aplicaciones' in data: # Allows sending empty list to clear
                juegos[i]['aplicaciones'] = data.get('aplicaciones')
            if 'componentes' in data: # Allows sending empty list to clear
                juegos[i]['componentes'] = data.get('componentes')
            
            with open(DATA_FILE_JUEGOS, 'w') as f:
                json.dump(juegos, f, indent=4)
            return juegos[i]
    return None

def delete_juego(juego_id):
    juegos = get_all_juegos()
    original_length = len(juegos)
    juegos = [juego for juego in juegos if juego['id'] != juego_id]
    if len(juegos) < original_length:
        with open(DATA_FILE_JUEGOS, 'w') as f:
            json.dump(juegos, f, indent=4)
        return True
    return False

# Modify add_product and update_product for multiple images and applications
# The product structure in product_catalog.json will now need to store:
# - 'image_filenames': a list of up to 5 image filenames (e.g., ["img1.jpg", None, "img3.jpg", ...])
# - 'aplicaciones': a list of application dicts, e.g., 
#   [{'vehiculo': 'Hilux', 'marca': 'Toyota', 'codigoJuego': 'J001', 'nombreJuego': 'Kit Embrague Hilux'}]

# Helper to manage image filenames list (up to 5)
def _update_image_filenames_list(existing_filenames, new_image_file, slot_index, product_id_for_filename=None):
    """
    Updates the list of image filenames.
    `existing_filenames` should be a list of 5 elements (can be None).
    `new_image_file` is the FileStorage object for the current slot.
    `slot_index` is 0-4.
    `product_id_for_filename` can be used to make filenames more unique if needed.
    Returns the updated list and the filename of the newly saved image (if any).
    """
    if not existing_filenames:
        existing_filenames = [None] * 5
    else: # Ensure it's 5 elements
        existing_filenames = (existing_filenames + [None] * 5)[:5]

    saved_filename_for_slot = existing_filenames[slot_index] # Keep old if no new one

    if new_image_file and new_image_file.filename:
        # Potentially delete old image if it exists and is different
        if existing_filenames[slot_index]:
            old_image_path = os.path.join(IMAGE_UPLOAD_FOLDER, existing_filenames[slot_index])
            # Consider deleting only if new filename is different, or always if replacing slot
            # For simplicity, let's assume we always replace if a new file is provided for a slot.
            # Deletion of orphaned files if a product is deleted is handled in delete_product.
            # If updating, and new file is same name, it's an overwrite. If different name, old one might be orphaned if not handled.
            # For now, we don't delete the old image here explicitly to avoid complexity,
            # assuming `delete_product` or a cleanup utility handles orphaned files.
            # Or, if `secure_filename` generates unique names, this is less of an issue.
            pass
            
        # Create a more unique filename to avoid conflicts
        base, ext = os.path.splitext(secure_filename(new_image_file.filename))
        # Using product_id in filename can help, but product_id is generated after add_product is called.
        # For add_product, can use a temp UUID then rename, or just rely on secure_filename + timestamp/random.
        # For update_product, product_id is available.
        # Let's use a simple unique enough name for now:
        if product_id_for_filename:
             filename = f"{base}_{product_id_for_filename}_slot{slot_index+1}{ext}"
        else: # For new products, product_id isn't known yet for filename uniqueness
             filename = f"{base}_{uuid.uuid4().hex[:8]}_slot{slot_index+1}{ext}"
        filename = secure_filename(filename) # Ensure it's still secure

        image_save_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
        new_image_file.save(image_save_path)
        saved_filename_for_slot = filename
    
    existing_filenames[slot_index] = saved_filename_for_slot
    return existing_filenames, saved_filename_for_slot


# Modify add_product
def add_product(data, image_files_list, aplicaciones_list=None): # image_files_list is a list of 5 FileStorage objects
    _ensure_image_upload_folder_exists()
    products = get_all_products()
    
    new_product_id = str(uuid.uuid4()) # Generate ID first for use in filenames

    current_image_filenames = [None] * 5
    if image_files_list and len(image_files_list) == 5:
        for i, image_file in enumerate(image_files_list):
            if image_file and image_file.filename: # Check if a file was actually uploaded for this slot
                # Pass product_id for more unique filenames
                updated_filenames, saved_name = _update_image_filenames_list(current_image_filenames, image_file, i, new_product_id)
                current_image_filenames = updated_filenames 
                # Note: _update_image_filenames_list modifies current_image_filenames directly at index i

    new_product = {
        'id': new_product_id,
        'product_code': data.get('product_code'),
        'name': data.get('name'),
        'brand_code': data.get('brand_code'), # Assuming data includes brand_code
        'category_code': data.get('category_code'), # Assuming data includes category_code
        'series': data.get('series'), # This is the series code/key
        'measurement': data.get('measurement'), # Assuming 'Medida' field
        'price_fox': data.get('price_fox'), # Keep for compatibility if still used
        'cost': data.get('cost'),
        'price_wholesale': data.get('price_wholesale'),
        'price_unit': data.get('price_unit'),
        'stock': data.get('stock'), # Assuming stock field
        'description': data.get('description'),
        'image_filenames': current_image_filenames, # List of up to 5 image filenames
        'image_filename': current_image_filenames[0] if any(current_image_filenames) else None, # Keep primary image for compatibility
        'aplicaciones': aplicaciones_list if aplicaciones_list else []
    }
    products.append(new_product)
    with open(DATA_FILE, 'w') as f:
        json.dump(products, f, indent=4)
    return new_product

# Modify update_product
# `images_data` could be a list of dicts: [{'file': FileStorage or None, 'removed': bool, 'current_filename': str or None}]
def update_product(product_id, data, images_data_list=None, aplicaciones_list=None):
    _ensure_image_upload_folder_exists()
    products = get_all_products()
    product_found = False
    updated_product_data = None

    for i, product in enumerate(products):
        if product['id'] == product_id:
            # Image handling
            current_image_filenames = product.get('image_filenames', [None]*5)
            if not isinstance(current_image_filenames, list) or len(current_image_filenames) != 5: # Ensure it's a list of 5
                current_image_filenames = ([None]*5 + current_image_filenames[:5] if isinstance(current_image_filenames, list) else [None]*5)[:5]


            if images_data_list and len(images_data_list) == 5:
                new_filenames_after_update = list(current_image_filenames) # Start with existing
                for slot_idx, image_info in enumerate(images_data_list):
                    # image_info = {'file': FileStorage or None, 'removed': bool, 'current_filename': str_or_None }
                    
                    # If image explicitly marked for removal
                    if image_info.get('removed') and new_filenames_after_update[slot_idx]:
                        old_image_path = os.path.join(IMAGE_UPLOAD_FOLDER, new_filenames_after_update[slot_idx])
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                            except OSError as e:
                                print(f"Error deleting image {old_image_path}: {e}")
                        new_filenames_after_update[slot_idx] = None
                    
                    # If a new file is provided for this slot
                    if image_info.get('file') and image_info['file'].filename:
                        # If there was an old image in this slot (even if different from current_filename due to prior changes not saved)
                        # and it's different from the one we are about to save, delete it.
                        if new_filenames_after_update[slot_idx]: # An image exists in this slot
                             # Path to the image currently recorded for this slot
                            image_to_potentially_delete = os.path.join(IMAGE_UPLOAD_FOLDER, new_filenames_after_update[slot_idx])
                            # The new file will get a name like `base_productid_slotX.ext`
                            # So, the old one should be removed if it existed.
                            if os.path.exists(image_to_potentially_delete):
                                try:
                                    os.remove(image_to_potentially_delete)
                                except OSError as e:
                                    print(f"Error deleting old image {image_to_potentially_delete} for slot {slot_idx}: {e}")
                            new_filenames_after_update[slot_idx] = None # Clear slot before new name

                        # Save the new file and update the filename for this slot
                        # _update_image_filenames_list expects a list and modifies it at index
                        # It's simpler here to call it with a temporary list for one slot or adapt its usage.
                        # For now, direct save:
                        new_file = image_info['file']
                        base, ext = os.path.splitext(secure_filename(new_file.filename))
                        new_filename = secure_filename(f"{base}_{product_id}_slot{slot_idx+1}{ext}")
                        new_file.save(os.path.join(IMAGE_UPLOAD_FOLDER, new_filename))
                        new_filenames_after_update[slot_idx] = new_filename
                
                current_image_filenames = new_filenames_after_update

            products[i]['image_filenames'] = current_image_filenames
            products[i]['image_filename'] = current_image_filenames[0] if any(current_image_filenames) else None # Primary image for compatibility
            
            # Update other fields
            products[i]['product_code'] = data.get('product_code', product['product_code'])
            products[i]['name'] = data.get('name', product['name'])
            products[i]['brand_code'] = data.get('brand_code', product.get('brand_code'))
            products[i]['category_code'] = data.get('category_code', product.get('category_code'))
            products[i]['series'] = data.get('series', product['series'])
            products[i]['measurement'] = data.get('measurement', product.get('measurement'))
            products[i]['price_fox'] = data.get('price_fox', product['price_fox']) # Keep for compatibility
            products[i]['cost'] = data.get('cost', product['cost'])
            products[i]['price_wholesale'] = data.get('price_wholesale', product['price_wholesale'])
            products[i]['price_unit'] = data.get('price_unit', product['price_unit'])
            products[i]['stock'] = data.get('stock', product.get('stock'))
            products[i]['description'] = data.get('description', product.get('description'))
            
            if aplicaciones_list is not None: # Allow clearing aplicaciones with empty list
                products[i]['aplicaciones'] = aplicaciones_list
            
            product_found = True
            updated_product_data = products[i]
            break
            
    if product_found:
        with open(DATA_FILE, 'w') as f:
            json.dump(products, f, indent=4)
        return updated_product_data
    return None


# Modify delete_product to remove multiple images
def delete_product(product_id):
    products = get_all_products()
    product_to_delete = None
    for product in products:
        if product['id'] == product_id:
            product_to_delete = product
            break

    if not product_to_delete:
        return False

    # Delete all associated image files
    image_filenames_to_delete = product_to_delete.get('image_filenames', [])
    if not image_filenames_to_delete and product_to_delete.get('image_filename'): # Fallback for old structure
        image_filenames_to_delete = [product_to_delete.get('image_filename')]

    for filename in image_filenames_to_delete:
        if filename: # If slot is not None
            image_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError as e:
                    print(f"Error deleting image {image_path}: {e}") # Log this

    new_products = [p for p in products if p['id'] != product_id]
    if len(new_products) < len(products):
        with open(DATA_FILE, 'w') as f:
            json.dump(new_products, f, indent=4)
        return True
    return False

# Placeholder for brand data
def get_all_brands_data():
    """Returns a list of brand data."""
    # Example: [{'code': 'B001', 'name': 'Marca X'}, ...]
    # This would typically come from a DB or JSON file.
    return [
        {'code': 'B001', 'name': 'Marca Fox'},
        {'code': 'B002', 'name': 'Marca Global'},
        {'code': 'B003', 'name': 'Otra Marca'},
    ]
