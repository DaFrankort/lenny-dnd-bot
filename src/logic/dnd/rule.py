from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Rule(DNDEntry):
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "rule"
        self.emoji = "📜"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = f"{json['ruleType']} Rule"

        self.description = json["description"]


class RuleList(DNDEntryList[Rule]):
    type = Rule
    paths = ["rules.json"]
