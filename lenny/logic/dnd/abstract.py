import abc
import dataclasses
import io
import json
import os
from collections.abc import Iterable
from typing import Any, Generic, Literal, TypedDict, TypeVar

import discord
import rich
import rich.box
from discord.app_commands import Choice
from rapidfuzz import fuzz
from rich.console import Console
from rich.table import Table

from methods import ChoicedEnum

BASE_DATA_PATHS = ["./submodules/lenny-dnd-data/generated/official/", "./submodules/lenny-dnd-data/generated/partnered/"]


class DNDEntryType(str, ChoicedEnum):
    ACTION = "action"
    BACKGROUND = "background"
    CLASS = "class"
    CONDITION = "condition"
    CREATURE = "creature"
    DEITY = "deity"
    FEAT = "feat"
    HAZARD = "hazard"
    ITEM = "item"
    LANGUAGE = "language"
    OBJECT = "object"
    RULE = "rule"
    SPECIES = "species"
    SPELL = "spell"
    TABLE = "table"
    VEHICLE = "vehicle"
    CULT = "cult"
    BOON = "boon"
    SKILL = "skill"

    @property
    def emoji(self) -> str:
        emojis = {
            self.ACTION: "🏃",
            self.BACKGROUND: "📕",
            self.CLASS: "🧙‍♂️",
            self.CONDITION: "🤒",
            self.CREATURE: "🐉",
            self.DEITY: "👁️",
            self.FEAT: "🎖️",
            self.HAZARD: "🪤",
            self.ITEM: "🗡️",
            self.LANGUAGE: "💬",
            self.OBJECT: "🪨",
            self.RULE: "📜",
            self.SPECIES: "🧝",
            self.SPELL: "🔥",
            self.TABLE: "📊",
            self.VEHICLE: "⛵",
            self.CULT: "🕯️",
            self.BOON: "🎁",
            self.SKILL: "🎯",
        }
        return emojis.get(self, "❓")


@dataclasses.dataclass
class FuzzyMatchResult:
    starts_with: bool  # Did the value start with the query
    score: float  # The score of the fuzzy match
    choice: Choice[str]  # The Choice object, as result to be used for discord


def fuzzy_matches(query: str, value: str, fuzzy_threshold: float = 75) -> FuzzyMatchResult | None:
    """Perform a fuzzy check between  a query and a value, e.g. searching for 'fire' in 'Fireball'.

    Args:
        query (str): The query to search for. In the example above this would be 'fire'.
        value (str): The value to search in. In the example above this would be 'Fireball'.
        fuzzy_threshold (float): A fuzziness threshold to determine how similar two words need to be.

    Returns:
        Optional[FuzzyMatchResult]: A fuzzy match result with the internals, or None if the threshold was not met.
    """
    query_clean = query.strip().lower().replace(" ", "")
    value_clean = value.strip().lower().replace(" ", "")
    score = fuzz.partial_ratio(query_clean, value_clean)
    starts_with = value_clean.startswith(query_clean)

    if score < fuzzy_threshold:
        return None
    return FuzzyMatchResult(starts_with=starts_with, score=score, choice=Choice(name=value, value=value))


class DescriptionRowRange(TypedDict):
    type: Literal["range"]
    min: int
    max: int


class DescriptionTable(TypedDict):
    headers: list[str] | None
    rows: list[Iterable[str] | DescriptionRowRange]


class Description(TypedDict):
    name: str
    type: Literal["text", "table"]
    value: str | DescriptionTable


class DNDEntry(abc.ABC):
    entry_type: str
    name: str
    source: str
    url: str | None
    emoji: DNDEntryType
    select_description: str | None = None  # Description in dropdown menus

    @abc.abstractmethod
    def __init__(self, obj: dict[str, Any]) -> None:
        pass

    @property
    def title(self) -> str:
        return f"{self.name} ({self.source})"


TDND = TypeVar("TDND", bound=DNDEntry)  # pylint: disable=invalid-name


class DNDEntryList(abc.ABC, Generic[TDND]):
    type: type
    paths: list[str]
    entries: list[TDND]

    def __init__(self):
        if not hasattr(self, "type"):
            raise NotImplementedError(f"Type not defined for '{self.__class__.__name__}'!")
        if not hasattr(self, "paths"):
            raise NotImplementedError(f"No data paths defined for '{self.__class__.__name__}'!")

        self.entries = []
        for path in self.paths:
            for base_path in BASE_DATA_PATHS:
                full_path = base_path + path
                for data in self.read_dnd_data_contents(full_path):
                    entry: TDND = self.type(data)
                    self.entries.append(entry)

    @staticmethod
    def read_dnd_data_contents(path: str) -> list[dict[str, Any]]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"D&D data file not found: '{path}'")
        if not os.path.isfile(path):
            raise TypeError(f"D&D data file is not a file: '{path}'")
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get(self, query: str, allowed_sources: set[str], fuzzy_threshold: float = 75) -> list[TDND]:
        query = query.strip().lower()
        exact: list[TDND] = []
        fuzzy: list[TDND] = []

        for entry in self.entries:
            if entry.source not in allowed_sources:
                continue

            entry_name = entry.name.strip().lower()
            if entry_name == query:
                exact.append(entry)
            if fuzz.ratio(query, entry_name) > fuzzy_threshold:
                fuzzy.append(entry)

        exact = sorted(exact, key=lambda e: (e.name, e.source))
        fuzzy = sorted(fuzzy, key=lambda e: (e.name, e.source))

        if len(exact) > 0:
            return exact
        return fuzzy

    def get_autocomplete_suggestions(
        self, query: str, allowed_sources: set[str], fuzzy_threshold: float = 75, limit: int = 25
    ) -> list[discord.app_commands.Choice[str]]:
        query = query.strip().lower().replace(" ", "")

        if query == "":
            return []

        choices: list[FuzzyMatchResult] = []
        seen_names: set[str] = set()  # Required to avoid duplicate suggestions
        for e in self.entries:
            if e.source not in allowed_sources:
                continue
            if e.name in seen_names:
                continue

            choice = fuzzy_matches(query, e.name, fuzzy_threshold)
            if choice is not None:
                choices.append(choice)
                seen_names.add(e.name)

        # Sort by query match => fuzzy score => alphabetically
        choices.sort(key=lambda x: (-x.starts_with, -x.score, x.choice.name))
        return [choice.choice for choice in choices[:limit]]

    def search(self, query: str, allowed_sources: set[str], fuzzy_threshold: float = 75) -> list[DNDEntry]:
        query = query.strip().lower()
        found: list[DNDEntry] = []

        for entry in self.entries:
            if entry.source not in allowed_sources:
                continue

            entry_name = entry.name.strip().lower()
            if fuzz.partial_ratio(query, entry_name) > fuzzy_threshold:
                found.append(entry)

        found = sorted(found, key=lambda e: (e.name, e.source))
        return found


def build_table(value: str | DescriptionTable, width: int | None = 56, show_lines: bool = False) -> str:
    if isinstance(value, str):
        return value

    def format_cell_value(value: int | str | dict[str, Any]) -> str:
        if isinstance(value, int):
            return str(value)
        if isinstance(value, str):
            return value
        if value["type"] == "range":
            if value["min"] == value["max"]:
                return str(value["min"])
            return f"{value['min']}-{value['max']}"
        raise ValueError("Unsupported cell type")

    headers = value["headers"]
    rows = value["rows"]

    box_style = rich.box.SQUARE_DOUBLE_HEAD if show_lines else rich.box.ROUNDED
    has_headers = headers is not None
    table = Table(box=box_style, show_lines=show_lines, show_header=has_headers)

    if has_headers:
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
    headers: list[str] | None,
    rows: list[Iterable[str]],
    width: int | None = 56,
    show_lines: bool = False,
) -> str:
    return build_table({"headers": headers, "rows": rows}, width, show_lines)
