import logging
import os
import json


BASE_PATH = "./assets/localisation"
LANGUAGES = ["english"]


def init_localisation():
    """Generates localisation templates for each language."""
    if not os.path.exists(BASE_PATH):
        os.makedirs(BASE_PATH)
        logging.info(f"Created localisation directory at {BASE_PATH}")

    for language in LANGUAGES:
        template = LocalisationTemplate()
        path = f"{BASE_PATH}/{language}.json"

        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as file:
                json.dump(template.json, file, indent=4, ensure_ascii=False)
                logging.info(f"Created template for {language} at {path}")
        else:
            pass  # TODO, Check if template up-to-date (?)

    logging.info("Initialised localisation templates.")


class FieldInfo:
    def __init__(self, name: str, description: list[str]):
        self.name = name
        self._descriptions = description

    @property
    def description(self) -> str:
        return "\n".join(self._descriptions)


class LocalisationBank:
    _data = {}

    @classmethod
    def load(cls):
        """Loads the localisation file for the specified language."""
        for language in LANGUAGES:
            path = f"{BASE_PATH}/{language}.json"
            if not os.path.exists(path):
                logging.warning(f"Localisation file for {language} does not exist at {path}.")
                continue

            with open(path, "r", encoding="utf-8") as file:
                cls._data[language] = json.load(file)
                logging.info(f"Loaded localisation data for {language}.")

    @classmethod
    def _get_language_data(cls, language: str):
        return cls._data.get(language, {})

    @classmethod
    def _get_help_data(cls, language: str):
        return cls._get_language_data(language).get("help", {})

    @classmethod
    def get_default_help_text(cls, language: str = LANGUAGES[0]) -> str:
        return cls._get_help_data(language).get("default_tab_text", "UNDEFINED")

    @classmethod
    def get_help_info(cls, tab_name: str, language: str = LANGUAGES[0]) -> list[FieldInfo]:
        field_info = cls._get_help_data(language).get("tab_fields", {}).get(tab_name, None)
        if field_info is None:
            return [FieldInfo("UNDEFINED", ["UNDEFINED"])]

        result = []
        for field in field_info:
            name = field.get("name", "UNDEFINED")
            desc = field.get("description", ["UNDEFINED"])
            if isinstance(desc, str):
                desc = [desc]
            result.append(FieldInfo(name, desc))
        return result


class _HelpTemplate():
    def __init__(self):
        self.default_text = "#TODO This bot provides a wide range of handy 5th edition Dungeon & Dragons commands, to help you with your games."
        self.fields = self.get_fields()

    def get_fields(self):
        from help import HelpTabs

        fields = {}
        for tab in HelpTabs:
            if tab == HelpTabs.Default:
                continue  # Default has special formatting

            fields[tab.name] = [
                    {
                        "name": "#TODO Subtitle",
                        "description": ["#TODO Field Description"],
                    }
                ]

        return fields

    def to_dict(self):
        return {
            "default_tab_text": self.default_text,
            "tab_fields": self.fields
        }


class LocalisationTemplate:
    def __init__(self):
        self.json = {
            "help": _HelpTemplate().to_dict()
        }
