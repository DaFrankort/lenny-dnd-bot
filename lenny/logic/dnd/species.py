from typing import Any

from logic.dnd.abstract import (
    Description,
    DNDEntry,
    DNDEntryList,
    DNDEntryType,
    ProficiencyOptions,
)


class Species(DNDEntry):
    image: str | None
    sizes: list[str]
    speed: list[str]
    type: str | None

    description: list[Description]
    info: list[Description]
    skill_prof: ProficiencyOptions | None

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.SPECIES

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.image = obj["image"]
        self.sizes = obj["sizes"]
        self.speed = obj["speed"]
        self.type = obj["creatureType"]

        self.description = obj["description"]
        self.info = obj["info"]

        skill_prof = obj["skillProficiencies"]
        if skill_prof:
            self.skill_prof = ProficiencyOptions(options=skill_prof["options"], amount=skill_prof["amount"])
        else:
            self.skill_prof = None


class SpeciesList(DNDEntryList[Species]):
    type = Species
    paths = ["species.json"]
