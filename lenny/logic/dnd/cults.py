from typing import Any

from logic.dnd.abstract import DNDEntryType, Description, DNDEntry, DNDEntryList


class Cult(DNDEntry):
    type: str
    goal: str | None
    cultists: str | None
    signature_spells: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]) -> None:
        self.entry_type = DNDEntryType.CULT

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.type = obj["type"]

        self.goal = obj.get("goal")
        self.cultists = obj.get("goal")
        self.signature_spells = obj.get("signatureSpells")
        self.description = obj["description"]


class CultList(DNDEntryList[Cult]):
    type = Cult
    paths = ["cults.json"]
