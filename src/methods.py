from abc import ABC, abstractmethod
from enum import Enum
import io
import json
import logging
import os
from typing import Iterable, TypeVar, Any
import discord
import rich
import rich.box
from rich.table import Table
from rich.console import Console
from PIL import ImageFont

T = TypeVar("T")
U = TypeVar("U")


def when(condition: bool | str | int | None, value_on_true: T, value_on_false: U) -> T | U:
    """Wrapper method for a ternary statement, for readability"""
    return value_on_true if condition else value_on_false


def build_table(value, width: int | None = 56, show_lines: bool = False) -> str:
    def format_cell_value(value: int | str | dict) -> str:
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, str):
            return value
        elif value["type"] == "range":
            if value["min"] == value["max"]:
                return str(value["min"])
            else:
                return f"{value['min']}-{value['max']}"
        raise Exception("Unsupported cell type")

    headers = value["headers"]
    rows = value["rows"]

    box_style = rich.box.SQUARE_DOUBLE_HEAD if show_lines else rich.box.ROUNDED
    table = Table(box=box_style, show_lines=show_lines)

    for header in headers:
        table.add_column(header, justify="left", style=None)

    for row in rows:
        formatted_row = [format_cell_value(value) for value in row]
        table.add_row(*formatted_row)

    buffer = io.StringIO()
    console = Console(file=buffer, width=width)
    console.print(table)
    table_string = f"```{buffer.getvalue()}```"
    buffer.close()

    return table_string


def build_table_from_rows(
    headers: list[str],
    rows: list[Iterable[str]],
    width: int | None = 56,
    show_lines: bool = False,
) -> str:
    return build_table({"headers": headers, "rows": rows}, width, show_lines)


class FontType(Enum):
    MONOSPACE = "./assets/fonts/GoogleSansCode-Light.ttf"
    FANTASY = "./assets/fonts/Merienda-Light.ttf"


def get_font(font: FontType, size: float):
    try:
        return ImageFont.truetype(font=font.value, size=size)
    except OSError:
        logging.warning(f"Font '{font.value}' could not be loaded!")
        return ImageFont.load_default(size=size)


class ChoicedEnum(Enum):
    @classmethod
    def choices(cls) -> list[discord.app_commands.Choice]:
        return [discord.app_commands.Choice(name=e.name.title(), value=e.value) for e in cls]

    @classmethod
    def values(cls) -> list[Any]:
        return [e.value for e in cls]


class JsonFileHandler(ABC):
    """
    Abstract base class for managing JSON-based file storage.

    This class provides a structured way to load and save data to JSON files.
    Subclasses define how raw JSON data is converted to and from internal
    Python objects via `load_from_json()` and `to_json_data()`.
    """

    _filename: str
    _basepath: str = "./temp"
    _subpath: str = ""
    data: Any

    def __init__(self, filename: str, subpath: str = ""):
        self._filename = filename
        self._subpath = subpath
        self.data = {}
        self.load()

    @property
    def path(self) -> str:
        if self._subpath:
            return os.path.join(self._basepath, self._subpath)
        return self._basepath

    @property
    def file_path(self) -> str:
        filename = f"{self._filename}.json"
        return os.path.join(self.path, filename)

    def load(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            logging.info(f"Created new filepath at: {self.path}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.load_from_json(data)
        except Exception as e:
            logging.warning(f"Failed to read file '{self.file_path}': {e}")
            self.data = {}

    def save(self):
        os.makedirs(self.path, exist_ok=True)
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
