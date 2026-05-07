import logging
from enum import Enum
from pathlib import Path

import discord

app_emojis = {}


def get_emoji_files() -> list[Path]:
    emoji_folder = Path("./assets/images/emojis")
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif"}
    return [file for file in emoji_folder.iterdir() if file.is_file() and file.suffix.lower() in valid_extensions]


def init_app_emojis(emojis: list[discord.Emoji]):
    global app_emojis

    app_emojis = {emoji.name: str(emoji) for emoji in emojis}


class AppEmoji(Enum):
    TEST = "dsa"

    # ENTRY TYPES
    ACTION = "action"
    BACKGROUND = "background"
    CLASS = "class"
    CONDITION = "condition"
    CREATURE = "creature"
    DEITY = "deity"
    FEAT = "feat"
    HAZARD = "hazard"
    ITEM = "item"
    LANGUAGE = "language"
    OBJECT = "object"
    RULE = "rule"
    SPECIES = "species"
    SPELL = "spell"
    TABLE = "table"
    VEHICLE = "vehicle"
    CULT = "cult"
    BOON = "boon"
    SKILL = "skill"

    @property
    def _fallback(self) -> str:
        fallback_map = {
            self.TEST: "🎲",
            # Entry Types
            self.ACTION: "🏃",
            self.BACKGROUND: "📕",
            self.CLASS: "🧙‍♂️",
            self.CONDITION: "🤒",
            self.CREATURE: "🐉",
            self.DEITY: "👁️",
            self.FEAT: "🎖️",
            self.HAZARD: "🪤",
            self.ITEM: "🗡️",
            self.LANGUAGE: "💬",
            self.OBJECT: "🪨",
            self.RULE: "📜",
            self.SPECIES: "🧝",
            self.SPELL: "🔥",
            self.TABLE: "📊",
            self.VEHICLE: "⛵",
            self.CULT: "🕯️",
            self.BOON: "🎁",
            self.SKILL: "🎯",
        }
        logging.warning(f"Used fallback emoji for '{self.value}'")
        return fallback_map.get(self, "❓")

    @property
    def emoji(self) -> str:
        return app_emojis.get(self.value, self._fallback)
