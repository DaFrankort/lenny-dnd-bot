from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Action(DNDEntry):
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "action"
        self.emoji = "🏃"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.select_description = obj["time"]

        self.description = obj["description"]


class ActionList(DNDEntryList[Action]):
    type = Action
    paths = ["actions.json"]
