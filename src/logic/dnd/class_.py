from logic.dnd.abstract import DNDObject, DNDObjectList, Description


class Class(DNDObject):
    subclass_unlock_level: int | None
    primary_ability: str | None
    spellcast_ability: str | None
    base_info: list[Description]
    level_resources: dict[str, list[Description]]
    level_features: dict[str, list[Description]]
    subclass_level_features: dict[str, dict[str, list[Description]]]

    def __init__(self, json: dict):
        self.object_type = "class"
        self.emoji = "🧙‍♂️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subclass_unlock_level = json["subclassUnlockLevel"]
        self.primary_ability = json["primaryAbility"]
        self.spellcast_ability = json["spellcastAbility"]
        self.base_info = json["baseInfo"]
        self.level_resources = json["levelResources"]
        self.level_features = json["levelFeatures"]
        self.subclass_level_features = json["subclassLevelFeatures"]

    def __repr__(self):
        return str(self)


class ClassList(DNDObjectList[Class]):
    path = "./submodules/lenny-dnd-data/generated/classes.json"

    def __init__(self):
        super().__init__()
        for character_class in self.read_dnd_data_contents(self.path):
            self.entries.append(Class(character_class))
