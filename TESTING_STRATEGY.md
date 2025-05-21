# Application Testing Strategy

This document outlines the testing strategy for the Flask ERP application. It covers general testing principles and specific testing approaches for each module.

## General Testing Principles

*   **Testing Framework:** We will use `pytest` along with `pytest-flask` for testing the Flask application. `pytest` provides a flexible and powerful testing framework.
*   **Unit Tests:** Unit tests will focus on individual functions and classes, particularly in `models.py` files. They will verify the correctness of business logic, data manipulation, and calculations.
*   **Functional Tests (Integration Tests):** Functional tests will target the application's routes and views. They will simulate HTTP requests (GET, POST) to test request handling, form processing, database interaction (mocked), template rendering, redirection, and flash messages. These tests ensure that different parts of the application work together correctly.
*   **Mocking:** External dependencies, especially file system operations (e.g., reading/writing JSON data files, image uploads), will be mocked using Python's `unittest.mock` library (or `pytest-mock`). This ensures that tests are isolated, repeatable, and do not have side effects on the actual file system. For image uploads, `werkzeug.datastructures.FileStorage` can be used to create mock file objects.
*   **Test Coverage:** Aim for high test coverage for both models and routes. Coverage tools (e.g., `pytest-cov`) will be used to measure this.
*   **Test Organization:** Tests will be organized in a `tests/` directory, with subdirectories mirroring the application's module structure (e.g., `tests/accounts_receivable/`, `tests/product_catalog/`).

---

## I. Accounts Receivable Module (`modules/accounts_receivable/`)

### Models (`models.py`)

*   **`_ensure_data_file_exists()`:**
    *   Test file creation if it doesn't exist.
    *   Test initialization with `[]` if file is empty or contains invalid JSON.
    *   Test no changes if file is valid.
*   **`get_all_entries()`:**
    *   Test with an empty data file (returns `[]`).
    *   Test with a populated data file (returns all entries).
*   **`add_entry(data)`:**
    *   Test adding a valid entry: data is saved correctly, ID is generated, returned entry is correct.
    *   Test data integrity: ensure other entries are not affected.
    *   Test that `uuid.uuid4` is called for ID generation.
*   **`get_entry_by_id(entry_id)`:**
    *   Test with a valid/existing `entry_id`.
    *   Test with a non-existent `entry_id` (returns `None`).
*   **`update_entry(entry_id, data)`:**
    *   Test updating an existing entry with valid data.
    *   Test updating specific fields (others remain unchanged).
    *   Test with a non-existent `entry_id` (returns `None`, no changes to file).
    *   Test data integrity after update.
*   **`delete_entry(entry_id)`:**
    *   Test deleting an existing entry (returns `True`, entry removed from file).
    *   Test with a non-existent `entry_id` (returns `False`, no changes to file).
    *   Test data integrity after deletion.

### Routes (`routes.py`)
*(All route tests will use the Flask test client provided by `pytest-flask` and mock the model functions.)*

*   **`/accounts_receivable/` (Index & Add Entry):**
    *   **GET:** Test successful response (200 OK), correct template (`ar_index.html`), display of existing entries (mocked).
    *   **POST (Add Entry):**
        *   Test successful entry creation with valid data: model's `add_entry` is called, flash message (`success`), redirection to index.
        *   Test with missing fields: no call to `add_entry`, flash message (`error`), re-renders form.
        *   Test with invalid amount (e.g., non-numeric): no call to `add_entry`, flash message (`error`), re-renders form.
*   **`/accounts_receivable/edit/<entry_id>` (Edit Entry):**
    *   **GET:**
        *   Test with existing entry ID: successful response (200 OK), correct template (`ar_edit_entry.html`), form pre-populated with entry data.
        *   Test with non-existent entry ID: flash message (`error`), redirection to index.
    *   **POST (Update Entry):**
        *   Test successful update with valid data: model's `update_entry` is called, flash message (`success`), redirection to index.
        *   Test with non-existent entry ID (though URL routing might prevent this, good to consider): flash message (`error`), redirection.
        *   Test with missing fields: no call to `update_entry`, flash message (`error`), re-renders edit form with existing data.
        *   Test with invalid amount: no call to `update_entry`, flash message (`error`), re-renders edit form.
*   **`/accounts_receivable/delete/<entry_id>` (Delete Entry):**
    *   **POST:**
        *   Test successful deletion with existing entry ID: model's `delete_entry` is called, flash message (`success`), redirection to index.
        *   Test deletion failure (e.g., `delete_entry` returns `False`): flash message (`error`), redirection to index.

---

## II. Cash and Banks Module (`modules/cash_and_banks/`)

### Models (`models.py`)

*   **`_ensure_data_file_exists()`:** (Similar tests as in Accounts Receivable)
*   **`get_all_transactions()`:**
    *   Test with empty/populated data file.
*   **`add_transaction(data)`:**
    *   Test adding valid cash and bank transactions.
    *   Ensure `amount` is correctly stored as float.
    *   Test ID generation.
*   **`get_transactions_by_date(date_str)`:**
    *   Test with a date that has transactions.
    *   Test with a date that has no transactions (returns `[]`).
    *   Test with various date formats if any flexibility is intended (though current implementation expects `YYYY-MM-DD`).
*   **`calculate_totals()`:**
    *   Test with no transactions (all totals are 0).
    *   Test with only cash transactions.
    *   Test with only bank transactions.
    *   Test with mixed transactions.
    *   Test with negative amounts if applicable (though current forms might prevent this).
*   **`calculate_daily_totals(date_str)`:**
    *   Test for a specific date with transactions (cash, bank, mixed).
    *   Test for a date with no transactions.

### Routes (`routes.py`)

*   **`/cash_and_banks/` (Index & Add Transaction):**
    *   **GET:** Test successful response, correct template (`cb_index.html`), display of transactions and overall totals (mocked model functions).
    *   **POST (Add Transaction):**
        *   Test successful transaction creation: `add_transaction` called, flash (`success`), redirect.
        *   Test form validation (required fields, numeric amount).
*   **`/cash_and_banks/daily_report/`:**
    *   **GET (no date query param):** Test successful response, correct template (`cb_daily_report.html`), no transactions displayed initially.
    *   **GET (with date query param):**
        *   Test with a date having transactions: `get_transactions_by_date` called, transactions displayed.
        *   Test with a date having no transactions: flash message (`info`), no transactions displayed.
        *   Test with invalid date format in query: flash message (`error`), page re-renders.
*   **`/cash_and_banks/corte_de_caja/`:**
    *   **GET:** Test successful response, correct template (`cb_corte_de_caja.html`), display of overall and today's totals (mock `calculate_totals` and `calculate_daily_totals`).

---

## III. Product Catalog Module (`modules/product_catalog/`)

### Models (`models.py`)

*   **`_ensure_data_file_exists()` & `_ensure_image_upload_folder_exists()`:**
    *   Test file/folder creation. (Mock `os.path.exists` and `os.makedirs`).
*   **`get_all_products()`:**
    *   Test with empty/populated data file.
*   **`add_product(data, image_file)`:**
    *   Test adding a product with and without an image.
    *   If image provided:
        *   Mock `image_file` (e.g., `werkzeug.datastructures.FileStorage`).
        *   Test `secure_filename` is called.
        *   Test `image_file.save` is called with the correct path.
        *   Test `image_filename` is stored in product data.
    *   Test ID generation.
*   **`get_product_by_id(product_id)`:** (Similar to Accounts Receivable)
*   **`update_product(product_id, data, image_file)`:**
    *   Test updating product details without changing the image.
    *   Test updating product details AND changing the image (new image saved, old one potentially deleted if logic implies, filename updated).
    *   Test updating with a new image when no previous image existed.
    *   Test clearing an existing image (if functionality allows, e.g., by not providing `image_file` and handling it, though current logic might not support explicit clearing without new image).
    *   Test with non-existent `product_id`.
    *   Mock file operations for image saving.
*   **`delete_product(product_id)`:**
    *   Test deleting a product with an associated image: `os.remove` called for the image, product removed from data.
    *   Test deleting a product without an image.
    *   Test with non-existent `product_id`.
    *   Mock `os.remove` and `os.path.exists`.
*   **`get_products_by_series(series_name)`:**
    *   Test with a valid series name that has products.
    *   Test with a series name that has no products.
    *   Test with `None` or empty `series_name` (returns all products).
*   **`PRODUCT_SERIES` constant:**
    *   Ensure it's accessible and contains expected values (though direct testing of a constant is minor).

### Routes (`routes.py`)

*   **`/products/` (List View) & `/products/grid/` (Grid View):**
    *   **GET:** Test successful response, correct templates (`pc_list_view.html`, `pc_grid_view.html`).
    *   Test display of products (mock `get_products_by_series`).
    *   Test with `series` query parameter for filtering: `get_products_by_series` called with correct series.
    *   Test display of `PRODUCT_SERIES` in filter dropdown.
*   **`/products/add/` (Add Product):**
    *   **GET:** Test form display, correct template (`pc_form.html`), `PRODUCT_SERIES` in form.
    *   **POST (Add Product):**
        *   Test successful creation with valid data and image: `add_product` called, flash (`success`), redirect.
        *   Test successful creation without an image.
        *   Test form validation (required fields, numeric prices/cost).
        *   Test image upload handling (mock `request.files`).
*   **`/products/edit/<product_id>/` (Edit Product):**
    *   **GET:**
        *   Test with existing ID: form pre-populated, image details displayed if any.
        *   Test with non-existent ID: flash (`error`), redirect.
    *   **POST (Update Product):**
        *   Test successful update with new data/image: `update_product` called, flash (`success`), redirect.
        *   Test form validation.
*   **`/products/delete/<product_id>/` (Delete Product):**
    *   **POST:** Test successful deletion: `delete_product` called, flash (`success`), redirect.

---

## IV. General Application Tests

*   **App Setup (`app.py`):**
    *   Test that the Flask app instance is created.
    *   Test that blueprints are registered correctly with their URL prefixes.
    *   Test that `app.config['UPLOAD_FOLDER']` is set.
    *   Test `app.secret_key` is set.
*   **Layout (`templates/layout.html`):**
    *   Using the test client, fetch a few pages and check for:
        *   Presence of the main navigation bar.
        *   Navigation links (`Home`, `Accounts Receivable`, etc.) point to the correct URLs (e.g., `url_for` resolves as expected).
        *   Presence of the main content container (`<div class="container">`).
        *   Flash message rendering area.
*   **Static Files:**
    *   Test that a request to `/static/css/style.css` returns a 200 OK response and the correct content type (`text/css`).
    *   If placeholder images or other static assets are critical, test their accessibility.
*   **Error Handling (General):**
    *   Test for 404 errors on undefined routes.
    *   (Future) Test any custom error pages if implemented.

---
This testing strategy will be revisited and updated as the application evolves.
