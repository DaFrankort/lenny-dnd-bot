from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList
from logic.roll import RollResult, roll


class DNDTable(DNDEntry):
    table: dict[str, Any]
    dice_notation: str | None
    footnotes: list[str] | None

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "table"
        self.emoji = "📊"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.dice_notation = json["roll"]
        self.table = json["table"]
        self.footnotes = json["footnotes"]

    @property
    def is_rollable(self) -> bool:
        return self.dice_notation is not None

    def roll(self) -> None | tuple[Any, RollResult]:
        if self.dice_notation is None:
            return None

        result = roll(self.dice_notation)
        rows = self.table["value"]["rows"]
        for row in rows:
            range = row[0]
            if range["min"] <= result.roll.total <= range["max"]:
                return row, result

        return None


class DNDTableList(DNDEntryList[DNDTable]):
    type = DNDTable
    paths = ["tables.json"]
