from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import os
from .models import (
    get_all_products, add_product, get_product_by_id,
    update_product, delete_product, get_products_by_series,
    PRODUCT_SERIES, IMAGE_UPLOAD_FOLDER
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
@product_catalog_bp.route('/list/', methods=['GET'])
def list_products():
    series_filter = request.args.get('series', None)
    products = get_products_by_series(series_filter)
    return render_template('pc_list_view.html', products=products, product_series_list=PRODUCT_SERIES, current_series=series_filter)

@product_catalog_bp.route('/grid/', methods=['GET'])
def grid_products():
    series_filter = request.args.get('series', None)
    products = get_products_by_series(series_filter)
    return render_template('pc_grid_view.html', products=products, product_series_list=PRODUCT_SERIES, current_series=series_filter)

@product_catalog_bp.route('/add/', methods=['GET', 'POST'])
def add_product_route():
    if request.method == 'POST':
        product_data = {
            'product_code': request.form.get('product_code'),
            'name': request.form.get('name'),
            'price_fox': request.form.get('price_fox'),
            'cost': request.form.get('cost'),
            'price_wholesale': request.form.get('price_wholesale'),
            'price_unit': request.form.get('price_unit'),
            'series': request.form.get('series')
        }
        
        image_file = request.files.get('image')

        if not all([product_data['product_code'], product_data['name'], product_data['series']]):
            flash('Product Code, Name, and Series are required.', 'error')
            # Pass current_app.config for UPLOAD_FOLDER if needed directly in template, or rely on static path construction
            return render_template('pc_form.html', product={}, product_series_list=PRODUCT_SERIES, form_action_url=url_for('product_catalog_bp.add_product_route'))

        # Basic validation for numeric fields
        try:
            if product_data['price_fox']: product_data['price_fox'] = float(product_data['price_fox'])
            if product_data['cost']: product_data['cost'] = float(product_data['cost'])
            if product_data['price_wholesale']: product_data['price_wholesale'] = float(product_data['price_wholesale'])
            if product_data['price_unit']: product_data['price_unit'] = float(product_data['price_unit'])
        except ValueError:
            flash('Invalid number format for one of the price/cost fields.', 'error')
            return render_template('pc_form.html', product=product_data, product_series_list=PRODUCT_SERIES, form_action_url=url_for('product_catalog_bp.add_product_route'))

        # Ensure UPLOAD_FOLDER is available
        _configure_upload_folder(current_app)

        add_product(product_data, image_file)
        flash('Product added successfully!', 'success')
        return redirect(url_for('product_catalog_bp.list_products'))

    return render_template('pc_form.html', product={}, product_series_list=PRODUCT_SERIES, form_action_url=url_for('product_catalog_bp.add_product_route'))


@product_catalog_bp.route('/edit/<string:product_id>/', methods=['GET', 'POST'])
def edit_product_route(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('product_catalog_bp.list_products'))

    if request.method == 'POST':
        product_data = {
            'product_code': request.form.get('product_code'),
            'name': request.form.get('name'),
            'price_fox': request.form.get('price_fox'),
            'cost': request.form.get('cost'),
            'price_wholesale': request.form.get('price_wholesale'),
            'price_unit': request.form.get('price_unit'),
            'series': request.form.get('series')
        }
        image_file = request.files.get('image')

        if not all([product_data['product_code'], product_data['name'], product_data['series']]):
            flash('Product Code, Name, and Series are required.', 'error')
            return render_template('pc_form.html', product=product, product_series_list=PRODUCT_SERIES, form_action_url=url_for('product_catalog_bp.edit_product_route', product_id=product_id))
        
        # Basic validation for numeric fields
        try:
            if product_data['price_fox']: product_data['price_fox'] = float(product_data['price_fox'])
            else: product_data['price_fox'] = None # Allow clearing
            if product_data['cost']: product_data['cost'] = float(product_data['cost'])
            else: product_data['cost'] = None
            if product_data['price_wholesale']: product_data['price_wholesale'] = float(product_data['price_wholesale'])
            else: product_data['price_wholesale'] = None
            if product_data['price_unit']: product_data['price_unit'] = float(product_data['price_unit'])
            else: product_data['price_unit'] = None
        except ValueError:
            flash('Invalid number format for one of the price/cost fields.', 'error')
            # Repopulate form with current (potentially invalid) data for correction
            current_form_data = product.copy()
            current_form_data.update(request.form.to_dict()) # Merge POSTed values
            return render_template('pc_form.html', product=current_form_data, product_series_list=PRODUCT_SERIES, form_action_url=url_for('product_catalog_bp.edit_product_route', product_id=product_id))


        _configure_upload_folder(current_app) # Ensure UPLOAD_FOLDER is set

        updated_product = update_product(product_id, product_data, image_file)
        if updated_product:
            flash('Product updated successfully!', 'success')
        else:
            flash('Error updating product.', 'error') # Should not happen if product was found initially
        return redirect(url_for('product_catalog_bp.list_products'))

    return render_template('pc_form.html', product=product, product_series_list=PRODUCT_SERIES, form_action_url=url_for('product_catalog_bp.edit_product_route', product_id=product_id))


@product_catalog_bp.route('/delete/<string:product_id>/', methods=['POST'])
def delete_product_route(product_id):
    # Ensure UPLOAD_FOLDER is available for model to use
    _configure_upload_folder(current_app)
    
    if delete_product(product_id):
        flash('Product deleted successfully!', 'success')
    else:
        flash('Error deleting product or product not found.', 'error')
    return redirect(url_for('product_catalog_bp.list_products'))
