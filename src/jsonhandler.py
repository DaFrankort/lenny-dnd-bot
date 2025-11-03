from abc import ABC, abstractmethod
import dataclasses
import json
import logging
import os
from typing import Any, Generic, List, Sequence, TypeVar, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = Any

SupportedBaseTypes = Union[int, str, bool, None, DataclassInstance]
SerializedBaseTypes = Union[int, str, bool, None, dict[str, Any]]

SupportedTypes = Union[Sequence[SupportedBaseTypes], SupportedBaseTypes]
SerializedTypes = Union[SerializedBaseTypes, List["SerializedBaseTypes"]]

T = TypeVar("T", bound=SupportedTypes)


class JsonHandler(ABC, Generic[T]):
    """
    Abstract base class for managing JSON-based file storage.

    This class provides a structured way to load and save data to JSON files.
    Subclasses define how raw JSON data is converted to and from internal
    Python objects via `load_from_json()` and `to_json_data()`.
    """

    _filename: str
    _path: str
    data: dict[str, T]

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

    def load_from_json(self, data: dict[str, Any]):
        self.data = {k: self.deserialize(v) for k, v in data.items()}

    def to_json_data(self) -> Any:
        return {k: self.serialize(v) for k, v in self.data.items()}

    def serialize(self, obj: T) -> SerializedTypes:
        if isinstance(obj, (int, str, bool)):
            return obj
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, list):
            return [self.serialize(o) for o in obj]  # type: ignore
        if obj is None:
            return None

        raise ValueError(f"Unsupported JSON handler serialization type '{type(obj)}'")

    @abstractmethod
    def deserialize(self, obj: Any) -> T:
        raise NotImplementedError()
