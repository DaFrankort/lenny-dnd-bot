from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class OptionalFeature(DNDEntry):
    prerequisite: str | None
    type: str
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.OPTIONAL_FEAT

        super().__init__(obj)
        self.url = obj["url"]

        self.prerequisite = obj["prerequisite"]
        self.type = obj["type"]
        self.description = obj["description"]


class OptionalFeatureList(DNDEntryList[OptionalFeature]):
    type = OptionalFeature
    paths = ["optionalfeatures.json"]
