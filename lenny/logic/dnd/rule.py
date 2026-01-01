from typing import Any

from logic.dnd.abstract import DNDEntryType, Description, DNDEntry, DNDEntryList


class Rule(DNDEntry):
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "rule"
        self.emoji = DNDEntryType.RULE

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.select_description = f"{obj['ruleType']} Rule"

        self.description = obj["description"]


class RuleList(DNDEntryList[Rule]):
    type = Rule
    paths = ["rules.json"]
