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
        except (json.JSONDecodeError, ValueError, FileNotFoundError):
            with open(DATA_FILE, 'w') as f:
                json.dump([], f)

def get_all_transactions():
    _ensure_data_file_exists()
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def add_transaction(data):
    transactions = get_all_transactions()
    new_transaction = {
        'id': str(uuid.uuid4()),
        'date': data.get('date'), # Expected format YYYY-MM-DD
        'concept': data.get('concept'),
        'amount': float(data.get('amount')),
        'type': data.get('type') # 'cash' or 'bank_account'
    }
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
    today_cash = sum(t['amount'] for t in daily_transactions if t['type'] == 'cash')
    today_bank = sum(t['amount'] for t in daily_transactions if t['type'] == 'bank_account')
    return {
        'today_cash': today_cash,
        'today_bank': today_bank,
        'today_grand_total': today_cash + today_bank
    }
