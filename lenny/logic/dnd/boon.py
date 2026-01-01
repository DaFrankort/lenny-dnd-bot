from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Boon(DNDEntry):
    type: str
    signature_spells: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]) -> None:
        self.entry_type = "boon"
        self.emoji = "🎁"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.type = obj["type"]

        self.signature_spells = obj.get("signatureSpells")
        self.description = obj["description"]


class BoonList(DNDEntryList[Boon]):
    type = Boon
    paths = ["boons.json"]
