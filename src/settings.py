import os
import tomllib

import toml


DEFAULT_CONFIG = {
    "bank": {
        "ignored_account_names": [],
    },
    "data": {
        "data_dir": "data",
        "label_db": "data/labels.db",
    },
}


def load_settings(filepath="settings.toml"):
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write(toml.dumps(DEFAULT_CONFIG))
        return DEFAULT_CONFIG
    with open(filepath, "rb") as f:
        return tomllib.load(f)


settings = load_settings()

IGNORED_ACCOUNT_NAMES = settings.get("bank", {}).get("ignored_account_names", [])

DATA_DIR = settings.get("data", {}).get("data_dir")
if DATA_DIR is None:
    raise ValueError("Missing 'data_dir' in [data] section of settings.toml")

LABEL_DB = settings.get("data", {}).get("label_db")
if LABEL_DB is None:
    raise ValueError("Missing 'label_db' in [data] section of settings.toml")
