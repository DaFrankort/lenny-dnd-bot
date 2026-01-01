from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Hazard(DNDEntry):
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.HAZARD

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.select_description = obj["subtitle"]

        self.description = obj["description"]


class HazardList(DNDEntryList[Hazard]):
    type = Hazard
    paths = ["traps.json", "hazards.json"]
