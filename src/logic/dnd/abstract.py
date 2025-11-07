import abc
import json
import logging
import os
from typing import Any, Generic, Iterable, Literal, TypeVar, TypedDict, Union
import discord
from rapidfuzz import fuzz
import io
import rich
import rich.box
from rich.table import Table
from rich.console import Console


class DescriptionRowRange(TypedDict):
    type: Literal["range"]
    min: int
    max: int


class DescriptionTable(TypedDict):
    headers: list[str]
    rows: list[Iterable[str] | DescriptionRowRange]


class Description(TypedDict):
    name: str
    type: Literal["text", "table"]
    value: Union[str, DescriptionTable]


class DNDEntry(abc.ABC):
    entry_type: str
    name: str
    source: str
    url: str | None
    emoji: str = "❓"
    select_description: str | None = None  # Description in dropdown menus

    @property
    def title(self) -> str:
        return f"{self.name} ({self.source})"


TDND = TypeVar("TDND", bound=DNDEntry)


class DNDEntryList(abc.ABC, Generic[TDND]):
    entries: list[TDND]

    def __init__(self):
        self.entries = []

    @staticmethod
    def read_dnd_data_contents(path: str) -> list[dict[str, Any]]:
        if not os.path.exists(path):
            logging.warning(f"D&D data file not found: '{path}'")
            return []
        if not os.path.isfile(path):
            logging.warning(f"D&D data file is not a file: '{path}'")
            return []
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

        choices: list[tuple[bool, float, discord.app_commands.Choice[str]]] = []
        seen_names: set[str] = set()  # Required to avoid duplicate suggestions
        for e in self.entries:
            if e.source not in allowed_sources:
                continue
            if e.name in seen_names:
                continue

            name_clean = e.name.strip().lower().replace(" ", "")
            score = fuzz.partial_ratio(query, name_clean)
            if score > fuzzy_threshold:
                starts_with_query = name_clean.startswith(query)
                choices.append(
                    (
                        starts_with_query,
                        score,
                        discord.app_commands.Choice(name=e.name, value=e.name),
                    )
                )
                seen_names.add(e.name)

        choices.sort(key=lambda x: (-x[0], -x[1], x[2].name))  # Sort by query match => fuzzy score => alphabetically
        return [choice for _, _, choice in choices[:limit]]

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
