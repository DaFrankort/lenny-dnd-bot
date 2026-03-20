from collections.abc import Sequence
from typing import Any

from logic.dnd.abstract import (
    DescriptionRowRange,
    DescriptionTable,
    DNDEntry,
    DNDEntryList,
    DNDEntryType,
)
from logic.roll import roll


class DNDTable(DNDEntry):
    table: DescriptionTable
    dice_notation: str | None
    footnotes: list[str] | None

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.TABLE

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.dice_notation = obj["roll"]
        self.table = obj["table"]
        self.footnotes = obj["footnotes"]

    @property
    def is_rollable(self) -> bool:
        return self.dice_notation is not None

    def roll(self) -> tuple[Any, int]:
        if self.dice_notation is None:
            raise PermissionError("This table is not rollable.")

        result = roll(self.dice_notation).roll.total
        row = self.get_rollable_row(result)
        return row, result

    def get_rollable_row(self, value: int) -> Sequence[str | DescriptionRowRange | int | None]:
        if not self.is_rollable:
            raise PermissionError("This table is not rollable.")

        rows = self.table["table"]["rows"]

        for row in rows:
            row_range = row[0]
            if isinstance(row_range, str):
                # A row is only a string if it's a non-rollable table
                raise TypeError(f"Unexpected string found in D&D table rolling range: '{row_range}'.")

            if row_range is None:
                continue

            if isinstance(row_range, int):
                if row_range == value:
                    return row
                continue

            if row_range["min"] <= value <= row_range["max"]:
                return row

        raise LookupError(f"The value {value} is out of range for a {self.dice_notation} roll!")


class DNDTableList(DNDEntryList[DNDTable]):
    type = DNDTable
    paths = ["tables.json"]
