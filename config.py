import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".obsync"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "vault_path": str(Path.home() / "Documents" / "Obsidian"),
    "port": 8765,
    "device_name": os.uname()[1],  # hostname
    "auto_sync": True,
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config: dict):
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_vault_path():
    return Path(load_config()["vault_path"])

def get_device_name():
    return load_config()["device_name"]

def get_port():
    return load_config()["port"]

def get_auto_sync():
    return load_config()["auto_sync"]
