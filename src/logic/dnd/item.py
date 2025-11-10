from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Item(DNDEntry):
    value: str | None
    weight: str | None
    type: list[str]
    properties: list[str]
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "item"
        self.emoji = "🗡️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.value = json["value"]
        self.weight = json["weight"]
        self.type = json["type"]
        self.properties = json["properties"]
        self.description = json["description"]

    @property
    def formatted_value_weight(self) -> str | None:
        value_weight: list[str] = []
        if self.value is not None:
            value_weight.append(self.value)
        if self.weight is not None:
            value_weight.append(self.weight)

        if len(value_weight) == 0:
            return None
        return ", ".join(value_weight)

    @property
    def formatted_type(self) -> str | None:
        if len(self.type) == 0:
            return None
        return ", ".join(self.type).capitalize()

    @property
    def formatted_properties(self) -> str | None:
        if len(self.properties) == 0:
            return None
        return ", ".join(self.properties).capitalize()


class ItemList(DNDEntryList[Item]):
    type = Item
    paths = ["items.json"]
