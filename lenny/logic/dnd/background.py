from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Background(DNDEntry):
    abilities: list[str]
    feat: str | None
    skills: str | None
    tools: str | None
    languages: str | None
    equipment: str | None
    prerequisite: str | None
    description: list[Description]
    fluff: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.BACKGROUND

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.abilities = obj["abilities"] or []
        self.feat = obj["feat"]
        self.skills = obj["skills"]
        self.tools = obj["tools"]
        self.languages = obj["languages"]
        self.equipment = obj["equipment"]
        self.prerequisite = obj["prerequisite"]
        self.description = obj["description"]
        self.fluff = obj["fluff"]


class BackgroundList(DNDEntryList[Background]):
    type = Background
    paths = ["backgrounds.json"]
