from typing import Any

from logic.dnd.abstract import DNDEntryType, Description, DNDEntry, DNDEntryList


class Condition(DNDEntry):
    description: list[Description]
    image: str | None

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "condition"
        self.emoji = DNDEntryType.CONDITION

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.description = obj["description"]
        self.image = obj["image"]


class ConditionList(DNDEntryList[Condition]):
    type = Condition
    paths = ["conditions.json", "diseases.json"]
