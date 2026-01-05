from typing import Any

from logic.dnd.abstract import DNDEntry, DNDEntryList, DNDEntryType, DescriptionTable
from logic.roll import RollResult, roll


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

    def roll(self) -> None | tuple[Any, RollResult]:
        if self.dice_notation is None:
            return None

        result = roll(self.dice_notation)
        rows = self.table["table"]["rows"]
        for row in rows:
            row_range = row[0]
            if isinstance(row_range, str):
                raise ValueError(f"Unexpected string found in D&D table rolling range.")

            if row_range["min"] <= result.roll.total <= row_range["max"]:
                return row, result

        return None


class DNDTableList(DNDEntryList[DNDTable]):
    type = DNDTable
    paths = ["tables.json"]
