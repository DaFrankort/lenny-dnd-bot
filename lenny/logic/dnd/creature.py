from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Creature(DNDEntry):
    subtitle: str | None
    summoned_by_spell: str | None
    summoned_by_class: str | None
    token_url: str | None
    description: list[Description]
    stats: Description
    details: Description
    traits: list[Description]
    actions: list[Description]
    bonus_actions: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.CREATURE

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.subtitle = obj["subtitle"]
        self.summoned_by_spell = obj["summonedBySpell"]
        self.summoned_by_class = obj["summonedByClass"]
        self.token_url = obj["tokenUrl"]

        self.description = obj["description"]
        self.select_description = self.subtitle

        # Currently only summonable creatures require this data.
        self.stats = obj["stats"] if self.is_summonable else []  # type: ignore
        self.details = obj["details"] if self.is_summonable else []  # type: ignore
        self.traits = obj["traits"] if self.is_summonable else []  # type: ignore
        self.actions = obj["actions"] if self.is_summonable else []  # type: ignore
        self.bonus_actions = obj["bonusActions"] if self.is_summonable else []  # type: ignore

    @property
    def is_summonable(self):
        # TODO Only show if summonable for class, or also for spell?
        return self.summoned_by_class is not None


class CreatureList(DNDEntryList[Creature]):
    type = Creature
    paths = ["creatures.json"]
