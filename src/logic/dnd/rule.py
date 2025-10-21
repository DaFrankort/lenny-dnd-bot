from logic.dnd.abstract import DNDObject, DNDObjectList, DNDObjectTypes, Description


class Rule(DNDObject):
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = DNDObjectTypes.RULE.value

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = f"{json['ruleType']} Rule"

        self.description = json["description"]


class RuleList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/rules.json"

    def __init__(self):
        super().__init__(DNDObjectTypes.RULE.value)
        for rule in self.read_dnd_data_contents(self.path):
            self.entries.append(Rule(rule))
