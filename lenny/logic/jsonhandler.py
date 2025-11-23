import dataclasses
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import discord

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = Any

SupportedBaseTypes = int | float | str | bool | DataclassInstance
SerializedBaseTypes = int | float | str | bool | dict[str, Any]

SupportedTypes = Sequence[SupportedBaseTypes] | SupportedBaseTypes
SerializedTypes = Sequence["SerializedBaseTypes"] | SerializedBaseTypes

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
    _allow_save: bool
    data: dict[str, T]

    def __init__(self, filename: str, sub_dir: str = ""):
        base_dir = "./temp"
        self._filename = filename
        self._path = os.path.join(base_dir, sub_dir) if sub_dir else base_dir
        self._allow_save = True
        self.data = {}
        self.load()

    @property
    def file_path(self) -> str:
        filename = f"{self._filename}.json"
        return os.path.join(self._path, filename)

    def load(self):
        if not os.path.exists(self._path):
            os.makedirs(self._path)
            logging.info("Created new filepath at: %s", self._path)

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data: dict[str, Any] = json.load(file)
                self.data = {k: self.deserialize(v) for k, v in data.items()}
        except FileNotFoundError:
            logging.warning("File not found, new file created at: '%s'", self.file_path)
            self.data = {}
            self.save()
        except KeyError as e:
            logging.error("Failed to read '%s', saving will be disabled for this file!\n%s", self.file_path, e)
            self._allow_save = False
            self.data = {}

    def save(self):
        if not self._allow_save:
            raise RuntimeError(
                "Your command worked, but the information will not be retained on a restart.\nKeep a backup of your changes and reach out to the bot's host to resolve this!"
            )
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


class JsonFolderHandler(ABC):
    _data: dict[int, JsonHandler[Any]] = {}
    _last_accessed: dict[int, int] = {}

    @abstractmethod
    def _itr_key(self, itr: discord.Interaction) -> int:
        """
        Define which key to use from the Interaction. (guild_id, user_id, ...)
        Additionally raise any interaction-checks in case Interaction is not allowed.
        """

    @abstractmethod
    def _load(self, itr: discord.Interaction) -> JsonHandler[Any]:
        """Load a new JsonHandler instance."""

    def get(self, itr: discord.Interaction) -> JsonHandler[Any]:
        key = self._itr_key(itr)
        if key not in self._data:
            self._data[key] = self._load(itr)
        self._last_accessed[key] = int(time.time())
        return self._data[key]

    def clear_cache(self):
        now = int(time.time())
        max_age = 30 * 60  # Seconds (30 minutes)
        threshold = now - max_age
        for key in self.keys:
            last_accessed = self._last_accessed.get(key, 0)
            if last_accessed < threshold:
                self._last_accessed.pop(key, None)
                self._data.pop(key, None)

    @property
    def keys(self) -> set[int]:
        return set(self._data.keys())
