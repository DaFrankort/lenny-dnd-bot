from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class DNDObject(DNDEntry):
    description: list[Description]
    token_url: str

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "object"
        self.emoji = "🪨"

        self.name = obj["name"]
        self.source = obj["source"]
        self.select_description = obj["subtitle"]
        self.url = obj["url"]
        self.token_url = obj["tokenUrl"]

        self.description = obj["description"]


class DNDObjectList(DNDEntryList[DNDObject]):
    type = DNDObject
    paths = ["objects.json"]
