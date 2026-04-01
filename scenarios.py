import json
import os
from datetime import datetime

SAVES_DIR = "saved_scenarios"


def ensure_saves_dir():
    """Create saves directory if it doesn't exist"""
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR)

def get_saved_scenarios():
    """Get list of saved scenario files"""
    ensure_saves_dir()
    files = [f.replace('.json', '') for f in os.listdir(SAVES_DIR) if f.endswith('.json')]
    return sorted(files)

def save_scenario(name, assumptions, properties, debts, financial_events=None):
    """Save current scenario to a JSON file"""
    ensure_saves_dir()
    data = {
        'saved_at': datetime.now().isoformat(),
        'assumptions': assumptions,
        'properties': properties,
        'debts': debts,
        'financial_events': financial_events or []
    }
    filepath = os.path.join(SAVES_DIR, f"{name}.json")
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    return filepath

def load_scenario(name):
    """Load a scenario from a JSON file"""
    filepath = os.path.join(SAVES_DIR, f"{name}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def delete_scenario(name):
    """Delete a saved scenario"""
    filepath = os.path.join(SAVES_DIR, f"{name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
