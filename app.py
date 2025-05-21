import os
from flask import Flask, render_template
from modules.accounts_receivable.routes import accounts_receivable_bp
from modules.cash_and_banks.routes import cash_and_banks_bp
from modules.product_catalog.routes import product_catalog_bp
# Correctly import IMAGE_UPLOAD_FOLDER from the models file where it's defined
from modules.product_catalog.models import IMAGE_UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Needed for flash messages

# Configure upload folder for product images
# Ensure the path is absolute or correctly relative to the app root.
# os.path.join(app.root_path, IMAGE_UPLOAD_FOLDER) is robust.
# IMAGE_UPLOAD_FOLDER is 'static/uploads/products/'
# app.root_path is the directory where app.py is.
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, IMAGE_UPLOAD_FOLDER)
# Ensure the directory exists (routes.py also does this, but good to have)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Register Blueprints
app.register_blueprint(accounts_receivable_bp, url_prefix='/accounts_receivable')
app.register_blueprint(cash_and_banks_bp, url_prefix='/cash_and_banks')
app.register_blueprint(product_catalog_bp, url_prefix='/products')


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
