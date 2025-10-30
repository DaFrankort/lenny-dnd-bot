from typing import Any
from logic.dnd.abstract import DNDObject, DNDObjectList
from logic.roll import RollResult, roll


class DNDTable(DNDObject):
    table: dict
    dice_notation: str | None
    footnotes: list[str] | None

    def __init__(self, json: dict):
        self.object_type = "table"
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


class DNDTableList(DNDObjectList[DNDTable]):
    path = "./submodules/lenny-dnd-data/generated/tables.json"

    def __init__(self):
        super().__init__()
        for table in self.read_dnd_data_contents(self.path):
            self.entries.append(DNDTable(table))
