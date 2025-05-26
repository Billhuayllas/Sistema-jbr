from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify 
from werkzeug.utils import secure_filename
import os
import json 
import uuid # For cloning
from .models import (
    get_all_products, add_product, get_product_by_id,
    update_product, delete_product, get_products_by_series,
    PRODUCT_SERIES, IMAGE_UPLOAD_FOLDER, 
    get_all_series_data, get_all_brands_data, get_all_categories_data, 
    get_all_juegos, model_add_juego, model_get_juego_by_id, 
    model_update_juego, model_delete_juego,
    # CRUD for Series
    get_all_series, add_serie, get_serie_by_id, update_serie, delete_serie,
    # CRUD for Categories
    get_all_categories, add_category, get_category_by_id, update_category, delete_category,
    # CRUD for Marcas
    get_all_marcas, add_marca, get_marca_by_id, update_marca, delete_marca
)

product_catalog_bp = Blueprint(
    'product_catalog_bp',
    __name__,
    template_folder='../../templates/product_catalog',
    static_folder='../../static' # This allows access to global static
    # static_url_path='/product_catalog/static' # if you need specific static for this blueprint
)

# Helper to ensure UPLOAD_FOLDER is configured at app level
def _configure_upload_folder(app):
    app.config['UPLOAD_FOLDER'] = IMAGE_UPLOAD_FOLDER # Defined in models.py
    # Ensure the folder exists (though models.py also does this)
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@product_catalog_bp.before_app_first_request
def setup_upload_folder():
    _configure_upload_folder(current_app)


@product_catalog_bp.route('/', methods=['GET']) # Changed to root of blueprint
@product_catalog_bp.route('/list/', methods=['GET']) # This will be our "priceTableView"
def list_products():
    _configure_upload_folder(current_app) # Ensure upload folder is configured
    
    search_query = request.args.get('search', None)
    all_products_data = get_all_products()

    if search_query:
        search_query_lower = search_query.lower()
        # This search can be expanded to include brand/series names if those are stored directly in product dict after resolving
        all_products_data = [
            p for p in all_products_data
            if search_query_lower in p.get('name', '').lower() or \
               search_query_lower in p.get('product_code', '').lower() or \
               (p.get('description') and search_query_lower in p.get('description', '').lower()) or \
               (p.get('series') and search_query_lower in p.get('series', '').lower()) # Assuming series code/name is searched
            # Add brand search if product.brand_code exists and brands_list allows lookup here (TODO if needed)
        ]
    
    series_map, _ = get_all_series_data() # We only need the map for resolving series names
    brands_list = get_all_brands_data() # List of brand dicts
    brands_map = {brand['code']: brand for brand in brands_list} 
    categories_list_for_table = get_all_categories_data() # Fetch categories for table view context

    return render_template(
        'pc_list_view.html', 
        products=all_products_data, 
        series_map=series_map, 
        brands_map=brands_map,
        categories_list=categories_list_for_table, # For the modal's category dropdown
        search_query=search_query
    )

# The main import at the top of the file is now the single source for model functions.
# No duplicate import block should exist.

@product_catalog_bp.route('/grid/', methods=['GET'])
def grid_products():
    _configure_upload_folder(current_app) 
    
    search_query = request.args.get('search', None)
    series_filter = request.args.get('series', None) 
    
    all_products = get_all_products() 
    
    if search_query:
        search_query_lower = search_query.lower()
        all_products = [
            p for p in all_products 
            if search_query_lower in p.get('name', '').lower() or \
               search_query_lower in p.get('product_code', '').lower() or \
               (p.get('description') and search_query_lower in p.get('description', '').lower())
        ]

    if series_filter:
        all_products = get_products_by_series(series_filter) 

    series_map, series_list_for_dropdown = get_all_series_data() 
    brands_list = get_all_brands_data() 
    categories_list = get_all_categories_data() # Fetch categories

    return render_template(
        'pc_grid_view.html', 
        products=all_products, 
        series_map=series_map, 
        series_list_for_dropdown=series_list_for_dropdown, 
        brands_list=brands_list, 
        categories_list=categories_list, # Pass categories to grid view context
        current_series_filter=series_filter, 
        search_query=search_query
    )

@product_catalog_bp.route('/add/', methods=['POST']) # Changed to POST only for AJAX
def add_product_route():
    _configure_upload_folder(current_app)
    
    form_data = request.form.to_dict()
    image_files = [request.files.get(f'productImage{i}') for i in range(1, 6)] # Get up to 5 images

    aplicaciones_json = request.form.get('aplicaciones_data', '[]')
    try:
        aplicaciones_list = json.loads(aplicaciones_json)
        if not isinstance(aplicaciones_list, list):
             return jsonify(success=False, message='Formato de aplicaciones inválido.'), 400
    except json.JSONDecodeError:
        return jsonify(success=False, message='Error decodificando aplicaciones JSON.'), 400
    
    # Basic validation
    required_fields = ['product_code', 'name', 'brand_code', 'category_code', 'series']
    missing_fields = [field for field in required_fields if not form_data.get(field)]
    if missing_fields:
        return jsonify(success=False, message=f'Campos obligatorios faltantes: {", ".join(missing_fields)}.'), 400

    # Convert numeric fields
    numeric_fields = {'price_unit': float, 'price_wholesale': float, 'cost': float, 'stock': int}
    for field, type_converter in numeric_fields.items():
        value = form_data.get(field)
        if value: # Only convert if value is provided
            try:
                form_data[field] = type_converter(value)
            except ValueError:
                return jsonify(success=False, message=f'Valor inválido para el campo {field}.'), 400
        else: # Handle optional numeric fields (e.g., set to None or 0)
            form_data[field] = None # Or 0, based on model's expectation

    new_product = add_product(form_data, image_files, aplicaciones_list)
    if new_product:
        return jsonify(success=True, message='Producto agregado exitosamente!', product=new_product) # Return new product data
    else:
        return jsonify(success=False, message='Error al agregar el producto.'), 500


@product_catalog_bp.route('/details/<string:product_id>/', methods=['GET'])
def get_product_details_json(product_id):
    product = get_product_by_id(product_id)
    if product:
        # Ensure fields expected by modal are present, even if None
        product.setdefault('image_filenames', [None]*5)
        if not isinstance(product['image_filenames'], list) or len(product['image_filenames']) != 5: # Ensure it's list of 5
             product['image_filenames'] = (product['image_filenames'] + [None]*5)[:5] if isinstance(product['image_filenames'], list) else [None]*5
        
        product.setdefault('aplicaciones', [])
        product.setdefault('measurement', '')
        product.setdefault('stock', 0)
        # Ensure numeric fields are numbers or None (not empty strings)
        for field in ['price_unit', 'price_wholesale', 'cost', 'stock']:
            if product.get(field) == '': product[field] = None
        
        return jsonify(product)
    return jsonify(error="Producto no encontrado"), 404


@product_catalog_bp.route('/edit/<string:product_id>/', methods=['POST']) # Changed to POST only for AJAX
def edit_product_route(product_id):
    _configure_upload_folder(current_app)
    
    product_to_edit = get_product_by_id(product_id)
    if not product_to_edit:
        return jsonify(success=False, message='Producto no encontrado para editar.'), 404

    form_data = request.form.to_dict()
    
    images_data_list = []
    for i in range(5): # Slots 0 to 4
        slot_idx = i # 0-indexed for list access
        image_file = request.files.get(f'productImage{slot_idx+1}') # HTML form fields are 1-indexed
        was_removed = request.form.get(f'removeImage{slot_idx}', 'no') == 'yes'
        current_filename_in_slot = request.form.get(f'currentImageFilename{slot_idx}', None)
        
        images_data_list.append({
            'file': image_file, 
            'removed': was_removed,
            'current_filename': current_filename_in_slot
        })

    aplicaciones_json = request.form.get('aplicaciones_data', '[]')
    try:
        aplicaciones_list = json.loads(aplicaciones_json)
        if not isinstance(aplicaciones_list, list):
             return jsonify(success=False, message='Formato de aplicaciones inválido.'), 400
    except json.JSONDecodeError:
        return jsonify(success=False, message='Error decodificando aplicaciones JSON.'), 400

    required_fields = ['product_code', 'name', 'brand_code', 'category_code', 'series']
    missing_fields = [field for field in required_fields if not form_data.get(field)]
    if missing_fields:
        return jsonify(success=False, message=f'Campos obligatorios faltantes: {", ".join(missing_fields)}.'), 400

    numeric_fields = {'price_unit': float, 'price_wholesale': float, 'cost': float, 'stock': int}
    for field, type_converter in numeric_fields.items():
        value = form_data.get(field)
        if value:
            try:
                form_data[field] = type_converter(value)
            except ValueError:
                 return jsonify(success=False, message=f'Valor inválido para el campo {field}.'), 400
        else:
            form_data[field] = None

    updated_product = update_product(product_id, form_data, images_data_list, aplicaciones_list)
    if updated_product:
        return jsonify(success=True, message='Producto actualizado exitosamente!', product=updated_product)
    else:
        return jsonify(success=False, message='Error al actualizar el producto.'), 500

# --- Rutas para Juegos de Productos ---

@product_catalog_bp.route('/juegos/', methods=['GET'])
def list_juegos():
    _configure_upload_folder(current_app) # In case it's needed by other parts of the page
    juegos_data = get_all_juegos()
    
    # For the "Add Component" Select2 in the modal, we need all individual products
    all_products_for_select = []
    raw_products = get_all_products() # Assuming this returns the list of product dicts
    for p in raw_products:
        all_products_for_select.append({
            'id': p.get('id'),
            'text': f"{p.get('name', 'N/A')} ({p.get('product_code', 'N/A')})", # Text for Select2
            'stock': p.get('stock', 0),
            'cost': p.get('cost', 0.0) # For calculating total cost in modal
        })
        
    return render_template(
        'pc_juegos_list.html', 
        juegos=juegos_data,
        all_products_for_select=json.dumps(all_products_for_select) # Pass as JSON string for JS
    )

@product_catalog_bp.route('/juegos/add', methods=['POST'])
def add_juego_route():
    data = request.get_json()
    if not data or not data.get('codigo') or not data.get('nombre'):
        return jsonify(success=False, message="Código y Nombre son obligatorios."), 400
    
    # Ensure 'aplicaciones' and 'componentes' are lists, even if empty
    data['aplicaciones'] = data.get('aplicaciones', [])
    data['componentes'] = data.get('componentes', [])

    new_juego = model_add_juego(data)
    if new_juego:
        return jsonify(success=True, message="Juego agregado exitosamente!", juego=new_juego)
    else:
        return jsonify(success=False, message="Error al agregar el juego."), 500

@product_catalog_bp.route('/juegos/details/<string:juego_id>', methods=['GET'])
def get_juego_details_json(juego_id):
    juego = model_get_juego_by_id(juego_id)
    if juego:
        return jsonify(juego)
    return jsonify(error="Juego no encontrado"), 404

@product_catalog_bp.route('/juegos/edit/<string:juego_id>', methods=['POST'])
def edit_juego_route(juego_id):
    data = request.get_json()
    if not data or not data.get('codigo') or not data.get('nombre'):
        return jsonify(success=False, message="Código y Nombre son obligatorios."), 400
    
    # Ensure 'aplicaciones' and 'componentes' are lists, even if not provided (to keep existing if not in data)
    # The model's update_juego handles this: only updates if key is present.
    
    updated_juego = model_update_juego(juego_id, data)
    if updated_juego:
        return jsonify(success=True, message="Juego actualizado exitosamente!", juego=updated_juego)
    else:
        return jsonify(success=False, message="Error al actualizar el juego o juego no encontrado."), 404 # Or 500

@product_catalog_bp.route('/juegos/delete/<string:juego_id>', methods=['POST'])
def delete_juego_route(juego_id):
    if model_delete_juego(juego_id):
        return jsonify(success=True, message="Juego eliminado exitosamente!")
    else:
        return jsonify(success=False, message="Error al eliminar el juego o juego no encontrado."), 404 # Or 500

@product_catalog_bp.route('/juegos/clone/<string:juego_id>', methods=['POST'])
def clone_juego_route(juego_id):
    original_juego = model_get_juego_by_id(juego_id)
    if not original_juego:
        return jsonify(success=False, message="Juego original no encontrado."), 404

    cloned_data = {
        'codigo': f"{original_juego.get('codigo', '')}-COPIA-{uuid.uuid4().hex[:4]}", # Ensure unique code
        'nombre': f"{original_juego.get('nombre', '')} (Copia)",
        'aplicaciones': list(original_juego.get('aplicaciones', [])), # Deep copy if list of dicts
        'componentes': list(original_juego.get('componentes', []))  # Deep copy if list of dicts
    }
    
    # For deep copy of list of dicts (if they contain mutable objects, though here they are simple dicts)
    cloned_data['aplicaciones'] = [dict(app) for app in cloned_data['aplicaciones']]
    cloned_data['componentes'] = [dict(comp) for comp in cloned_data['componentes']]

    new_juego = model_add_juego(cloned_data)
    if new_juego:
        return jsonify(success=True, message="Juego clonado exitosamente!", juego=new_juego)
    else:
        return jsonify(success=False, message="Error al clonar el juego."), 500

# --- Config Table Routes: Series ---
@product_catalog_bp.route('/config/series/', methods=['GET'])
def list_series_view():
    series_list = get_all_series()
    return render_template('pc_series_list.html', series_list=series_list)

@product_catalog_bp.route('/config/series/add', methods=['POST'])
def add_serie_route():
    data = request.get_json()
    if not data or not data.get('codigo') or not data.get('nombre'):
        return jsonify(success=False, message="Código y Nombre son obligatorios."), 400
    
    # Check for unique codigo (model should also do this, but good for early feedback)
    existing_series = get_all_series()
    if any(s['codigo'].lower() == data['codigo'].lower() for s in existing_series):
        return jsonify(success=False, message=f"El código de serie '{data['codigo']}' ya existe."), 409 # 409 Conflict

    new_serie = add_serie(data)
    if new_serie:
        return jsonify(success=True, message="Serie agregada exitosamente!", serie=new_serie)
    else: # Could be due to other model validation or file error
        return jsonify(success=False, message="Error al agregar la serie. Verifique los datos o el log del servidor."), 500

@product_catalog_bp.route('/config/series/details/<string:serie_id>', methods=['GET'])
def get_serie_details_route(serie_id):
    serie = get_serie_by_id(serie_id)
    if serie:
        return jsonify(serie)
    return jsonify(error="Serie no encontrada"), 404

@product_catalog_bp.route('/config/series/edit/<string:serie_id>', methods=['POST'])
def edit_serie_route(serie_id):
    data = request.get_json()
    if not data or not data.get('nombre'): # Codigo is not editable via this route
        return jsonify(success=False, message="Nombre es obligatorio."), 400
    
    updated_serie = update_serie(serie_id, data)
    if updated_serie:
        return jsonify(success=True, message="Serie actualizada exitosamente!", serie=updated_serie)
    else:
        return jsonify(success=False, message="Error al actualizar la serie o serie no encontrada."), 404 # Or 500

@product_catalog_bp.route('/config/series/delete/<string:serie_id>', methods=['POST'])
def delete_serie_route(serie_id):
    # TODO: Add check if series is in use by products before deleting
    if delete_serie(serie_id):
        return jsonify(success=True, message="Serie eliminada exitosamente!")
    else:
        return jsonify(success=False, message="Error al eliminar la serie o serie no encontrada."), 404

# --- Config Table Routes: Categories ---
@product_catalog_bp.route('/config/categories/', methods=['GET'])
def list_categories_view():
    categories_list = get_all_categories()
    return render_template('pc_categories_list.html', categories_list=categories_list)

@product_catalog_bp.route('/config/categories/add', methods=['POST'])
def add_category_route():
    data = request.get_json()
    if not data or not data.get('nombre'):
        return jsonify(success=False, message="Nombre es obligatorio."), 400
    
    existing_categories = get_all_categories()
    if any(c['nombre'].lower() == data['nombre'].lower() for c in existing_categories):
        return jsonify(success=False, message=f"La categoría '{data['nombre']}' ya existe."), 409

    new_category = add_category(data)
    if new_category:
        return jsonify(success=True, message="Categoría agregada exitosamente!", category=new_category)
    else:
        return jsonify(success=False, message="Error al agregar la categoría."), 500

@product_catalog_bp.route('/config/categories/details/<string:category_id>', methods=['GET'])
def get_category_details_route(category_id):
    category = get_category_by_id(category_id)
    if category:
        return jsonify(category)
    return jsonify(error="Categoría no encontrada"), 404

@product_catalog_bp.route('/config/categories/edit/<string:category_id>', methods=['POST'])
def edit_category_route(category_id):
    data = request.get_json()
    if not data or not data.get('nombre'):
        return jsonify(success=False, message="Nombre es obligatorio."), 400
    
    # Check for name uniqueness if it's being changed (model also does this)
    # This is a simplified version; more robust check in model is preferred.

    updated_category = update_category(category_id, data)
    if updated_category:
        return jsonify(success=True, message="Categoría actualizada exitosamente!", category=updated_category)
    else:
        return jsonify(success=False, message="Error al actualizar la categoría o categoría no encontrada."), 404

@product_catalog_bp.route('/config/categories/delete/<string:category_id>', methods=['POST'])
def delete_category_route(category_id):
    # TODO: Add check if category is in use by products
    if delete_category(category_id):
        return jsonify(success=True, message="Categoría eliminada exitosamente!")
    else:
        return jsonify(success=False, message="Error al eliminar la categoría o categoría no encontrada."), 404

# --- Config Table Routes: Marcas (Brands) ---
@product_catalog_bp.route('/config/marcas/', methods=['GET'])
def list_marcas_view():
    marcas_list = get_all_marcas()
    return render_template('pc_marcas_list.html', marcas_list=marcas_list)

@product_catalog_bp.route('/config/marcas/add', methods=['POST'])
def add_marca_route():
    data = request.get_json()
    if not data or not data.get('nombre'):
        return jsonify(success=False, message="Nombre es obligatorio."), 400

    existing_marcas = get_all_marcas()
    if any(m['nombre'].lower() == data['nombre'].lower() for m in existing_marcas):
        return jsonify(success=False, message=f"La marca '{data['nombre']}' ya existe."), 409

    new_marca = add_marca(data)
    if new_marca:
        return jsonify(success=True, message="Marca agregada exitosamente!", marca=new_marca)
    else:
        return jsonify(success=False, message="Error al agregar la marca."), 500

@product_catalog_bp.route('/config/marcas/details/<string:marca_id>', methods=['GET'])
def get_marca_details_route(marca_id):
    marca = get_marca_by_id(marca_id)
    if marca:
        return jsonify(marca)
    return jsonify(error="Marca no encontrada"), 404

@product_catalog_bp.route('/config/marcas/edit/<string:marca_id>', methods=['POST'])
def edit_marca_route(marca_id):
    data = request.get_json()
    if not data or not data.get('nombre'):
        return jsonify(success=False, message="Nombre es obligatorio."), 400
    
    updated_marca = update_marca(marca_id, data)
    if updated_marca:
        return jsonify(success=True, message="Marca actualizada exitosamente!", marca=updated_marca)
    else:
        return jsonify(success=False, message="Error al actualizar la marca o marca no encontrada."), 404

@product_catalog_bp.route('/config/marcas/delete/<string:marca_id>', methods=['POST'])
def delete_marca_route(marca_id):
    # TODO: Add check if marca is in use by products
    if delete_marca(marca_id):
        return jsonify(success=True, message="Marca eliminada exitosamente!")
    else:
        return jsonify(success=False, message="Error al eliminar la marca o marca no encontrada."), 404


@product_catalog_bp.route('/delete/<string:product_id>/', methods=['POST'])
def delete_product_route(product_id):
    # Ensure UPLOAD_FOLDER is available for model to use
    _configure_upload_folder(current_app)
    
    if delete_product(product_id):
        flash('Product deleted successfully!', 'success')
    else:
        flash('Error deleting product or product not found.', 'error')
    return redirect(url_for('product_catalog_bp.list_products'))
