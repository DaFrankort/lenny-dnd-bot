from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class DNDObject(DNDEntry):
    description: list[Description]
    token_url: str

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "object"
        self.emoji = "🪨"

        self.name = json["name"]
        self.source = json["source"]
        self.select_description = json["subtitle"]
        self.url = json["url"]
        self.token_url = json["tokenUrl"]

        self.description = json["description"]


class DNDObjectList(DNDEntryList[DNDObject]):
    type = DNDObject
    paths = ["objects.json"]
