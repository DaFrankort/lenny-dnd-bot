from typing import Any

from logic.dnd.abstract import DNDEntryType, Description, DNDEntry, DNDEntryList


class Creature(DNDEntry):
    subtitle: str | None
    summoned_by_spell: str | None
    token_url: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "creature"
        self.emoji = DNDEntryType.CREATURE

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.subtitle = obj["subtitle"]
        self.summoned_by_spell = obj["summonedBySpell"]
        self.token_url = obj["tokenUrl"]
        self.description = obj["description"]

        self.select_description = self.subtitle


class CreatureList(DNDEntryList[Creature]):
    type = Creature
    paths = ["creatures.json"]
