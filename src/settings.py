import os
import tomllib
import toml

DEFAULT_CONFIG = {
    "bank": {"ignored_account_names": []},
    "data": {"data_dir": "data", "label_db": "data/labels.db"},
    "ui": {"theme": "light"},
}

def load_settings(filepath="settings.toml"):
    if not os.path.exists(filepath):
        save_settings(filepath, DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(filepath, "rb") as f:
        return tomllib.load(f)

def reload_globals():
    global IGNORED_ACCOUNT_NAMES, DATA_DIR, LABEL_DB, UI_THEME
    IGNORED_ACCOUNT_NAMES = settings.get("bank", {}).get("ignored_account_names", [])
    DATA_DIR = settings.get("data", {}).get("data_dir")
    if DATA_DIR is None:
        raise ValueError("Missing 'data_dir' in [data] section of settings.toml")
    LABEL_DB = settings.get("data", {}).get("label_db")
    if LABEL_DB is None:
        raise ValueError("Missing 'label_db' in [data] section of settings.toml")
    UI_THEME = settings.get("ui", {}).get("theme", "light")

def save_settings(filepath="settings.toml", data=None):
    global settings
    if data is None:
        data = settings
    with open(filepath, "w") as f:
        f.write(toml.dumps(data))
    settings = load_settings(filepath)
    reload_globals()

def set_theme(theme: str):
    if theme not in ("dark", "light"):
        raise ValueError("Theme must be 'dark' or 'light'")
    settings.setdefault("ui", {})["theme"] = theme
    save_settings()

settings = load_settings()
reload_globals()
