# ERP System - Accounts, Cash/Banks, Product Catalog

A Flask-based web application providing basic ERP functionalities including:
*   Accounts Receivable Management
*   Cash and Bank Transaction Tracking
*   Product Catalog Management with Image Uploads

## Prerequisites

*   Python 3.6+
*   pip (Python package installer)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    # If you haven't already, clone the repository to your local machine.
    # git clone <repository-url>
    # cd <repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install dependencies:**
    Make sure you are in the project root directory where `requirements.txt` is located.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Ensure your virtual environment is activated.**
2.  **Run the Flask development server:**
    From the project root directory:
    ```bash
    python app.py
    ```
    Alternatively, you can use the Flask CLI:
    ```bash
    flask run
    ```
3.  **Open your web browser** and navigate to the URL provided by Flask (usually `http://127.0.0.1:5000/`).

## Features Overview

*   **Home Page:** Basic welcome page with navigation.
*   **Accounts Receivable (`/accounts_receivable/`):**
    *   Add, view, edit, and delete accounts receivable entries.
    *   Data stored in `accounts_receivable.json`.
*   **Cash and Banks (`/cash_and_banks/`):**
    *   Add and view cash/bank transactions.
    *   View overall totals for cash and bank accounts.
    *   Generate daily reports for transactions.
    *   Perform a "Corte de Caja" (Cash Reconciliation) for current day and overall totals.
    *   Data stored in `cash_and_banks.json`.
*   **Product Catalog (`/products/`):**
    *   Add, view, edit, and delete products.
    *   Upload product images (stored in `static/uploads/products/`).
    *   Categorize products by series.
    *   View products in list and grid layouts.
    *   Data stored in `product_catalog.json`.

## Project Structure

*   `app.py`: Main Flask application file.
*   `modules/`: Contains blueprints for different application modules.
    *   `accounts_receivable/`
    *   `cash_and_banks/`
    *   `product_catalog/`
*   `templates/`: HTML templates for rendering pages.
*   `static/`: Static files (CSS, images).
*   `requirements.txt`: Python dependencies.
*   `TESTING_STRATEGY.md`: Document outlining the approach for testing the application.
*   `*.json`: Data files used by the application modules (created automatically).
```
