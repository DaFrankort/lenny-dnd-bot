from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Rule(DNDEntry):
    description: list[Description]

    def __init__(self, json: dict):
        self.entry_type = "rule"
        self.emoji = "📜"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = f"{json['ruleType']} Rule"

        self.description = json["description"]


class RuleList(DNDEntryList[Rule]):
    path = "./submodules/lenny-dnd-data/generated/rules.json"

    def __init__(self):
        super().__init__()
        for rule in self.read_dnd_data_contents(self.path):
            self.entries.append(Rule(rule))
