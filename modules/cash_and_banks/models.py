import json
import uuid
import os
from datetime import datetime

DATA_FILE = 'cash_and_banks.json'

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
        except (json.JSONDecodeError, ValueError, FileNotFoundError): # More specific error catching
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)

def get_all_transactions():
    _ensure_data_file_exists()
    try:
        with open(DATA_FILE, 'r') as f:
            transactions = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        transactions = []

    normalized_transactions = []
    for t in transactions:
        # 1. Map 'concept' to 'descripcion'
        if 'concept' in t and 'descripcion' not in t:
            t['descripcion'] = t.pop('concept')
        t.setdefault('descripcion', '')

        # 2. Handle 'amount' and 'tipo_movimiento'
        original_amount = t.get('amount', 0.0)
        try:
            original_amount = float(original_amount)
        except (ValueError, TypeError):
            original_amount = 0.0 # Default if conversion fails

        if 'tipo_movimiento' not in t or t['tipo_movimiento'] not in ['Ingreso', 'Salida']:
            if original_amount < 0:
                t['tipo_movimiento'] = 'Salida'
                t['amount'] = abs(original_amount)
            else:
                t['tipo_movimiento'] = 'Ingreso' # Default for positive or zero old amounts
                t['amount'] = original_amount
        else: # tipo_movimiento exists, ensure amount is positive
            t['amount'] = abs(original_amount)
        
        # 3. Handle 'cuenta' (replaces 'type') and 'banco'
        if 'cuenta' not in t:
            old_type = t.pop('type', None)
            if old_type == 'cash':
                t['cuenta'] = 'Caja'
            elif old_type == 'bank_account':
                t['cuenta'] = 'CuentaBancaria'
            else:
                t['cuenta'] = 'General' # Default if no old type or unmappable
        
        t.setdefault('banco', None if t['cuenta'] != 'CuentaBancaria' else '') # Ensure 'banco' exists, empty if not applicable

        normalized_transactions.append(t)
    return normalized_transactions

def add_transaction(data): # Expects new structure: date, descripcion, amount (positive), tipo_movimiento, cuenta, [banco]
    transactions = get_all_transactions() # Gets normalized transactions, but we add new, already normalized one
    
    new_id = str(uuid.uuid4())
    amount = 0.0
    try:
        amount = abs(float(data.get('amount', 0.0))) # Ensure amount is positive
    except ValueError:
        # Handle error or log, for now default to 0.0
        # In a real app, this should probably raise an error or return None
        print(f"Warning: Invalid amount provided for add_transaction: {data.get('amount')}")

    new_transaction = {
        'id': new_id,
        'date': data.get('date'), 
        'descripcion': data.get('descripcion'),
        'amount': amount,
        'tipo_movimiento': data.get('tipo_movimiento', 'Ingreso'), # Default to Ingreso if not specified
        'cuenta': data.get('cuenta', 'General'), # Default to General
        'banco': data.get('banco') if data.get('cuenta') == 'CuentaBancaria' else None
    }
    
    # Basic validation for required fields
    if not all([new_transaction['date'], new_transaction['descripcion'], new_transaction['tipo_movimiento'], new_transaction['cuenta']]):
        # Handle error appropriately, e.g., raise ValueError or return None
        print(f"Error: Missing required fields for transaction. Data: {data}")
        return None


    transactions.append(new_transaction)
    with open(DATA_FILE, 'w') as f:
        json.dump(transactions, f, indent=4)
    return new_transaction

def get_transactions_by_date(date_str): # date_str in YYYY-MM-DD format
    transactions = get_all_transactions()
    return [t for t in transactions if t['date'] == date_str]

def calculate_totals():
    transactions = get_all_transactions()
    total_cash = sum(t['amount'] for t in transactions if t['type'] == 'cash')
    total_bank = sum(t['amount'] for t in transactions if t['type'] == 'bank_account')
    grand_total = total_cash + total_bank
    return {
        'total_cash': total_cash,
        'total_bank': total_bank,
        'grand_total': grand_total
    }

def calculate_daily_totals(date_str): # date_str in YYYY-MM-DD format
    daily_transactions = get_transactions_by_date(date_str)
    today_cash = sum(t['amount'] for t in daily_transactions if t.get('cuenta') == 'Caja') # Updated field name
    today_bank = sum(t['amount'] for t in daily_transactions if t.get('cuenta') == 'CuentaBancaria') # Updated field name
    return {
        'today_cash': today_cash,
        'today_bank': today_bank,
        'today_grand_total': today_cash + today_bank
        # This function might need to be replaced by calculate_saldo
    }

# New/Updated functions as per current subtask

def get_transaction_by_id(transaction_id): # Helper function if needed
    transactions = get_all_transactions() # Gets normalized transactions
    for t in transactions:
        if t['id'] == transaction_id:
            return t
    return None

def update_transaction(transaction_id, data):
    transactions = get_all_transactions() # Read and normalize all
    transaction_updated = False
    updated_tx_data = None

    for i, t in enumerate(transactions):
        if t['id'] == transaction_id:
            transactions[i]['date'] = data.get('date', t['date'])
            transactions[i]['descripcion'] = data.get('descripcion', t['descripcion'])
            
            try:
                amount = abs(float(data.get('amount', t['amount'])))
            except ValueError:
                amount = t['amount'] # Keep old if new is invalid
            transactions[i]['amount'] = amount
            
            transactions[i]['tipo_movimiento'] = data.get('tipo_movimiento', t['tipo_movimiento'])
            transactions[i]['cuenta'] = data.get('cuenta', t['cuenta'])
            
            if transactions[i]['cuenta'] == 'CuentaBancaria':
                transactions[i]['banco'] = data.get('banco', t.get('banco'))
            else:
                transactions[i]['banco'] = None
            
            # Basic validation
            if not all([transactions[i]['date'], transactions[i]['descripcion'], transactions[i]['tipo_movimiento'], transactions[i]['cuenta']]):
                 print(f"Error: Missing required fields during update for transaction ID {transaction_id}. Data: {data}")
                 return None # Or handle error differently

            transaction_updated = True
            updated_tx_data = transactions[i]
            break
    
    if transaction_updated:
        with open(DATA_FILE, 'w') as f:
            json.dump(transactions, f, indent=4)
        return updated_tx_data
    return None

def delete_transaction(transaction_id):
    transactions = get_all_transactions() # Read and normalize
    original_length = len(transactions)
    transactions = [t for t in transactions if t['id'] != transaction_id]
    if len(transactions) < original_length:
        with open(DATA_FILE, 'w') as f:
            json.dump(transactions, f, indent=4)
        return True
    return False

def get_transactions_by_account_type(cuenta_filter=None, banco_filter=None):
    transactions = get_all_transactions() # Already normalized
    
    if cuenta_filter:
        transactions = [t for t in transactions if t.get('cuenta') == cuenta_filter]
        if cuenta_filter == 'CuentaBancaria' and banco_filter:
            transactions = [t for t in transactions if t.get('banco') == banco_filter]
            
    return transactions

def calculate_saldo(transactions_list, filter_dict=None):
    """
    Calculates saldo for a list of transactions, optionally filtered.
    filter_dict can contain 'cuenta' and/or 'banco'.
    """
    if not transactions_list: # Should receive normalized transactions
        return 0.0

    filtered_transactions = transactions_list
    if filter_dict:
        if 'cuenta' in filter_dict:
            filtered_transactions = [t for t in filtered_transactions if t.get('cuenta') == filter_dict['cuenta']]
            if filter_dict['cuenta'] == 'CuentaBancaria' and 'banco' in filter_dict:
                filtered_transactions = [t for t in filtered_transactions if t.get('banco') == filter_dict['banco']]
    
    saldo = 0.0
    for t in filtered_transactions:
        amount = t.get('amount', 0.0)
        if t.get('tipo_movimiento') == 'Ingreso':
            saldo += amount
        elif t.get('tipo_movimiento') == 'Salida':
            saldo -= amount
    return saldo

# Old calculate_totals seems to be for a different structure.
# The new calculate_daily_totals might also need to be re-evaluated or replaced by calculate_saldo.
# For now, calculate_daily_totals is updated to use new field names, but its overall utility
# might be superseded by more flexible calculate_saldo calls.
# The `calculate_totals` function that summed total_cash and total_bank based on 'type'
# is effectively replaced by calling `calculate_saldo` with appropriate filters.
# e.g. calculate_saldo(all_transactions, {'cuenta': 'Caja'}) for total_cash.
