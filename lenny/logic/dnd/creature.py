from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Creature(DNDEntry):
    subtitle: str | None
    summoned_by_spell: str | None
    token_url: str | None
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "creature"
        self.emoji = "🐉"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subtitle = json["subtitle"]
        self.summoned_by_spell = json["summonedBySpell"]
        self.token_url = json["tokenUrl"]
        self.description = json["description"]

        self.select_description = self.subtitle


class CreatureList(DNDEntryList[Creature]):
    type = Creature
    paths = ["creatures.json"]
