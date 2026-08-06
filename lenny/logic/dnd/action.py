from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Action(DNDEntry):
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.ACTION

        super().__init__(obj)
        self.url = obj["url"]
        self.select_description = obj["time"]

        self.description = obj["description"]


class ActionList(DNDEntryList[Action]):
    type = Action
    paths = ["actions.json"]
