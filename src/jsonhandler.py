from abc import ABC, abstractmethod
import json
import logging
import os
from typing import Any


class JsonHandler(ABC):
    """
    Abstract base class for managing JSON-based file storage.

    This class provides a structured way to load and save data to JSON files.
    Subclasses define how raw JSON data is converted to and from internal
    Python objects via `load_from_json()` and `to_json_data()`.
    """

    _filename: str
    _path: str
    data: dict[str, Any]

    def __init__(self, filename: str, sub_dir: str = ""):
        base_dir = "./temp"
        self._filename = filename
        self._path = os.path.join(base_dir, sub_dir) if sub_dir else base_dir
        self.data = {}
        self.load()

    @property
    def file_path(self) -> str:
        filename = f"{self._filename}.json"
        return os.path.join(self._path, filename)

    def load(self):
        if not os.path.exists(self._path):
            os.makedirs(self._path)
            logging.info(f"Created new filepath at: {self._path}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.load_from_json(data)
        except Exception as e:
            logging.warning(f"Failed to read file '{self.file_path}': {e}")
            self.data = {}

    def save(self):
        os.makedirs(self._path, exist_ok=True)
        data = self.to_json_data()
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    @abstractmethod
    def load_from_json(self, data: Any):
        """
        Load JSON content into `self.data`.
        Called after reading the JSON file. Subclasses define how
        the raw `data` is processed and stored.
        """
        raise NotImplementedError

    @abstractmethod
    def to_json_data(self) -> Any:
        """
        Convert `self.data` to a JSON-serializable format.
        Called before saving to disk. Must return data suitable for `json.dump()`.
        """
        raise NotImplementedError
