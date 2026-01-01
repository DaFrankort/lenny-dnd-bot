from typing import Any

from logic.dnd.abstract import DNDEntryType, Description, DNDEntry, DNDEntryList


class Deity(DNDEntry):
    symbol_url: str | None
    inline_desc: list[Description]
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.DEITY

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.select_description = obj["subtitle"]
        self.inline_desc = obj["inlineDescription"]
        self.description = obj["description"]

        self.symbol_url = obj["imgUrl"]


class DeityList(DNDEntryList[Deity]):
    type = Deity
    paths = ["deities.json"]
