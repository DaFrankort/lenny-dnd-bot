import random
from dataclasses import dataclass

from logic.dnd.abstract import DNDEntryList


@dataclass
class LifeClass:
    name: str
    source: str
    reasons: list[str]
    other: dict[str, list[str]]


@dataclass
class LifeBackground:
    name: str
    source: str
    reasons: list[str]


class LifeData:
    path = "./submodules/lenny-dnd-data/generated/official/life.json"  # Data only available in official.
    classes: dict[str, LifeClass]
    backgrounds: dict[str, LifeBackground]
    trinkets: list[str]

    def __init__(self):
        self.classes = {}
        self.backgrounds = {}
        self.trinkets = []
        data = DNDEntryList.read_dnd_data_contents(self.path)

        for datum in data:
            class_data = datum.get("class", {})
            for class_name, details in class_data.items():
                self.classes[class_name] = LifeClass(
                    name=details.get("name"),
                    source=details.get("source"),
                    reasons=details.get("reasons", []),
                    other=details.get("other", {}),
                )

            background_data = datum.get("background", {})
            for bg_name, details in background_data.items():
                self.backgrounds[bg_name] = LifeBackground(
                    name=details.get("name"), source=details.get("source"), reasons=details.get("reasons", [])
                )

            self.trinkets.extend(datum.get("trinket", []))

    def get_random_class_reason(self, class_name: str) -> str | None:
        data = self.classes.get(class_name, None)
        if data is None:
            return None
        return random.choice(data.reasons)

    def get_random_class_others(self, class_name: str) -> list[tuple[str, str]] | None:
        data = self.classes.get(class_name, None)
        if data is None:
            return None
        others: list[tuple[str, str]] = []
        for key, entries in data.other.items():
            others.append((key, random.choice(entries)))
        return others

    def get_random_background_reason(self, background_name: str) -> str | None:
        data = self.backgrounds.get(background_name, None)
        if data is None:
            return None
        return random.choice(data.reasons)

    def get_random_trinket(self) -> str:
        return random.choice(self.trinkets)
