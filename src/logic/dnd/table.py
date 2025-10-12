from logic.dnd.abstract import DNDObject, DNDObjectList, Description
from logic.roll import RollResult, roll


class DNDTable(DNDObject):
    dice_notation: str | None
    table: Description
    footnotes: list[str] | None

    def __init__(self, json: any):
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

    def roll(self) -> None | tuple[any, RollResult]:
        if not self.is_rollable:
            return None

        result = roll(self.dice_notation)
        rows = self.table["value"]["rows"]
        for row in rows:
            range = row[0]
            if range["min"] <= result.roll.total <= range["max"]:
                return row, result

        return None


class DNDTableList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/tables.json"

    def __init__(self):
        super().__init__()
        for table in self.read_dnd_data_contents(self.path):
            self.entries.append(DNDTable(table))
