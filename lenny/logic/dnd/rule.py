from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Rule(DNDEntry):
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.RULE

        super().__init__(obj)
        self.url = obj["url"]
        self.select_description = f"{obj['ruleType']} Rule"

        self.description = obj["description"]


class RuleList(DNDEntryList[Rule]):
    type = Rule
    paths = ["rules.json"]
