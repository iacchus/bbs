import toml
import os
from typing import List, Dict

SERVERS_FILE = "servers.toml"

def load_servers() -> List[Dict]:
    if not os.path.exists(SERVERS_FILE):
        return []
    try:
        with open(SERVERS_FILE, "r") as f:
            data = toml.load(f)
        return data.get("servers", [])
    except Exception as e:
        print(f"Error loading servers: {e}")
        return []

def save_servers(servers: List[Dict]):
    try:
        with open(SERVERS_FILE, "w") as f:
            toml.dump({"servers": servers}, f)
    except Exception as e:
        print(f"Error saving servers: {e}")
