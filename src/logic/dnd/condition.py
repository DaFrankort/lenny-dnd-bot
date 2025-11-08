from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Condition(DNDEntry):
    description: list[Description]
    image: str | None

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "condition"
        self.emoji = "💀"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.description = json["description"]
        self.image = json["image"]


class ConditionList(DNDEntryList[Condition]):
    paths = [
        "./submodules/lenny-dnd-data/generated/conditions.json",
        "./submodules/lenny-dnd-data/generated/diseases.json",
    ]

    def __init__(self):
        super().__init__()
        for path in self.paths:
            data = self.read_dnd_data_contents(path)
            for condition in data:
                self.entries.append(Condition(condition))
