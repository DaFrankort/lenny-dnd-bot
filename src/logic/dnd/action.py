from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Action(DNDEntry):
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "action"
        self.emoji = "🏃"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["time"]

        self.description = json["description"]


class ActionList(DNDEntryList[Action]):
    type = Action
    paths = ["actions.json"]
