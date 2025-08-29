import json
import os

DB_FILE = 'database.json'

def load_db():
    """
    Loads the database from the JSON file.
    If the file doesn't exist, it creates a default structure.
    """
    if not os.path.exists(DB_FILE):
        print("Database file not found. Creating a new one.")
        return {'scanned_targets': [], 'found_vulnerabilities': []}

    print("Loading existing database...")
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Database file is corrupted. Starting fresh.")
            return {'scanned_targets': [], 'found_vulnerabilities': []}

def save_db(data):
    """Saves the given data to the database JSON file."""
    print("Saving database...")
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def add_vulnerability_record(db, target, vulnerability):
    """Adds a record of a found vulnerability to the database object."""
    db['found_vulnerabilities'].append({
        'target_name': target['name'],
        'vulnerability_type': vulnerability['type'],
        'severity': vulnerability['severity'],
        'payout': vulnerability['payout']
    })

def mark_target_as_scanned(db, target):
    """Adds a target's name to the list of scanned targets."""
    if target['name'] not in db['scanned_targets']:
        db['scanned_targets'].append(target['name'])
