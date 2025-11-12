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
    type = Condition
    paths = ["conditions.json", "diseases.json"]
