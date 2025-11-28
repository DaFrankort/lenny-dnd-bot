from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Language(DNDEntry):
    speakers: str | None
    script: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "language"
        self.emoji = "🗣️"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.select_description = obj["type"]

        self.speakers = obj["typicalSpeakers"]
        self.script = obj["script"]
        self.description = obj["description"]


class LanguageList(DNDEntryList[Language]):
    type = Language
    paths = ["languages.json"]
