import dataclasses
import json
import logging
import os
from typing import Any, Generic, Sequence, TypeVar, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = Any

SupportedBaseTypes = Union[int, float, str, bool, DataclassInstance]
SerializedBaseTypes = Union[int, float, str, bool, dict[str, Any]]

SupportedTypes = Union[Sequence[SupportedBaseTypes], SupportedBaseTypes]
SerializedTypes = Union[Sequence["SerializedBaseTypes"], SerializedBaseTypes]

T = TypeVar("T", bound=SupportedTypes)


class JsonHandler(Generic[T]):
    """
    Abstract base class for managing JSON-based file storage.

    This class provides a structured way to load and save data to JSON files.
    Subclasses define how raw JSON data is converted to and from internal
    Python objects via `serialize()` and `deserialize()`. Note that these functions
    work on *direct values*, so they must also be able to (de)serialize lists.
    Serialize has already been implemented, whereas deserialized has to be implemented
    in the subclass.
    """

    _filename: str
    _path: str
    data: dict[str, T]

    def __init__(self, filename: str, sub_dir: str = ""):
        base_dir = "./temp"
        self._filename = filename
        self._path = os.path.join(base_dir, sub_dir) if sub_dir else base_dir
        self.data = dict()
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
                data: dict[str, Any] = json.load(file)
                self.data = {k: self.deserialize(v) for k, v in data.items()}
        except FileNotFoundError as e:
            logging.warning(f"Failed to read file '{self.file_path}': {e}")
            self.data = {}

    def save(self):
        os.makedirs(self._path, exist_ok=True)
        data = {k: self.serialize(v) for k, v in self.data.items()}
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def serialize(self, obj: T) -> SerializedTypes:
        if isinstance(obj, (int, str, bool)):
            return obj
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, list):
            return [self.serialize(o) for o in obj]  # type: ignore

        raise ValueError(f"Unsupported JSON handler serialization type '{type(obj)}'")

    def deserialize(self, obj: Any) -> T:
        if isinstance(obj, (int, str, bool, float)):
            return obj  # type: ignore
        if isinstance(obj, list):
            return [self.deserialize(o) for o in obj]  # type: ignore

        raise NotImplementedError(
            f"Json handler deserialization is not implemented for {type(obj)} in {self.__class__.__name__}"
        )
