import toml
import os
from typing import List, Dict

IDENTITIES_FILE = "identities.toml"

def load_identities() -> List[Dict]:
    if not os.path.exists(IDENTITIES_FILE):
        return []
    try:
        with open(IDENTITIES_FILE, "r") as f:
            data = toml.load(f)
        return data.get("identities", [])
    except Exception as e:
        print(f"Error loading identities: {e}")
        return []

def save_identities(identities: List[Dict]):
    try:
        # Sort by name for consistency
        identities = sorted(identities, key=lambda x: x.get('name', ''))
        with open(IDENTITIES_FILE, "w") as f:
            toml.dump({"identities": identities}, f)
    except Exception as e:
        print(f"Error saving identities: {e}")

# Helper class to mimic IdentityRecord for easier migration
class IdentityRecord:
    def __init__(self, name, private_key, public_key=None):
        self.name = name
        self.private_key = private_key
        self.public_key = public_key

def get_all_identities_sync() -> List[IdentityRecord]:
    data = load_identities()
    return [IdentityRecord(name=i['name'], private_key=i['private_key'], public_key=i.get('public_key')) for i in data]

def add_identity_sync(name: str, private_key: str, public_key: str = None):
    identities = load_identities()
    # Check if exists
    if any(i['private_key'] == private_key for i in identities):
        return
    identities.append({
        "name": name,
        "private_key": private_key,
        "public_key": public_key
    })
    save_identities(identities)

def update_identity_name_sync(private_key: str, new_name: str):
    identities = load_identities()
    for i in identities:
        if i['private_key'] == private_key:
            i['name'] = new_name
            break
    save_identities(identities)

def delete_identity_sync(private_key: str):
    identities = load_identities()
    identities = [i for i in identities if i['private_key'] != private_key]
    save_identities(identities)
