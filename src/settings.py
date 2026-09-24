from pathlib import Path
from threading import Lock

import toml
import tomllib

DEFAULT_CONFIG = {
    "bank": {
        "ignored_account_names": [],
    },
    "data": {
        "data_dir": "data",
        "label_db": "data/labels.db",
    },
    "ui": {
        "theme": "light",
    },
}


class Settings:
    _instance = None
    _lock = Lock()

    def __new__(cls, filepath="settings.toml"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._filepath = Path(filepath)
                    instance._load()
                    cls._instance = instance
        return cls._instance

    def _load(self):
        if not self._filepath.exists():
            self._config = DEFAULT_CONFIG.copy()
            self.save()
            return

        with self._filepath.open("rb") as f:
            self._config = tomllib.load(f)

    def save(self):
        self._filepath.write_text(
            toml.dumps(self._config),
            encoding="utf-8",
        )

    @property
    def ignored_account_names(self):
        return self._config["bank"]["ignored_account_names"]

    @ignored_account_names.setter
    def ignored_account_names(self, value):
        self._config["bank"]["ignored_account_names"] = value
        self.save()

    @property
    def data_dir(self):
        return self._config["data"]["data_dir"]

    @data_dir.setter
    def data_dir(self, value):
        self._config["data"]["data_dir"] = value
        self.save()

    @property
    def label_db(self):
        return self._config["data"]["label_db"]

    @label_db.setter
    def label_db(self, value):
        self._config["data"]["label_db"] = value
        self.save()

    @property
    def theme(self):
        return self._config["ui"]["theme"]

    @theme.setter
    def theme(self, value):
        if value not in ("light", "dark"):
            raise ValueError("Theme must be 'dark' or 'light'")
        self._config["ui"]["theme"] = value
        self.save()


settings = Settings()
