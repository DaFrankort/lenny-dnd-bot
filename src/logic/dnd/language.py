from logic.dnd.abstract import DNDObject, DNDObjectList, DNDObjectTypes, Description


class Language(DNDObject):
    speakers: str | None
    script: str | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = DNDObjectTypes.LANGUAGE.value

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["type"]

        self.speakers = json["typicalSpeakers"]
        self.script = json["script"]
        self.description = json["description"]


class LanguageList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/languages.json"

    def __init__(self):
        super().__init__(DNDObjectTypes.LANGUAGE.value)
        for language in self.read_dnd_data_contents(self.path):
            self.entries.append(Language(language))
