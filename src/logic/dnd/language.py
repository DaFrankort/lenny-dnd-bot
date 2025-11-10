from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Language(DNDEntry):
    speakers: str | None
    script: str | None
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "dict"
        self.emoji = "🗣️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["type"]

        self.speakers = json["typicalSpeakers"]
        self.script = json["script"]
        self.description = json["description"]


class LanguageList(DNDEntryList[Language]):
    type = Language
    paths = ["languages.json"]
