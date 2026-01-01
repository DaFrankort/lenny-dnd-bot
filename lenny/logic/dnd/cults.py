from typing import Any

from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Cult(DNDEntry):
    type: str
    goal: str | None
    cultists: str | None
    signatureSpells: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]) -> None:
        self.entry_type = "cult"
        self.emoji = "🕯️"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.type = obj["type"]

        self.goal = obj.get("goal")
        self.cultists = obj.get("goal")
        self.signatureSpells = obj.get("signatureSpells")
        self.description = obj["description"]


class CultList(DNDEntryList[Cult]):
    type = Cult
    paths = ["cults.json"]
