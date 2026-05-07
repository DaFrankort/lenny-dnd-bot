import logging
from enum import Enum
from pathlib import Path

import discord

app_emojis = {}


def get_emoji_files() -> list[Path]:
    emoji_folder = Path("./assets/images/emojis")
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    return [file for file in emoji_folder.iterdir() if file.is_file() and file.suffix.lower() in valid_extensions]


def init_app_emojis(emojis: list[discord.Emoji]):
    global app_emojis

    app_emojis = {emoji.name: str(emoji) for emoji in emojis}


class AppEmoji(Enum):
    # DICE
    D20 = "d20"
    D12 = "d12"
    D10 = "d10"
    D8 = "d8"
    D6 = "d6"
    D4 = "d4"

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

    # Classes
    ARTIFICER = "classartificer"
    BARBARIAN = "classbarbarian"
    BARD = "classbard"
    CLERIC = "classcleric"
    DRUID = "classdruid"
    FIGHTER = "classfighter"
    MONK = "classmonk"
    PALADIN = "classpaladin"
    RANGER = "classranger"
    ROGUE = "classrogue"
    SORCERER = "classsorcerer"
    WARLOCK = "classwarlock"
    WIZARD = "classwizard"

    @property
    def _fallback(self) -> str:
        fallback_map = {
            # DICE
            self.D20: "🎲",
            self.D12: "🎲",
            self.D10: "🎲",
            self.D8: "🎲",
            self.D6: "🎲",
            self.D4: "🎲",
            # ENTRY TYPES
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
            # CLASSES
            self.ARTIFICER: "🛠️",
            self.BARBARIAN: "🪓",
            self.BARD: "🪈",
            self.CLERIC: "🙏",
            self.DRUID: "🌿",
            self.FIGHTER: "⚔️",
            self.MONK: "📿",
            self.PALADIN: "🛡️",
            self.RANGER: "🏹",
            self.ROGUE: "🗡️",
            self.SORCERER: "🌀",
            self.WARLOCK: "🌙",
            self.WIZARD: "📖",
        }
        logging.warning(f"Using fallback emoji for '{self.value}'")
        return fallback_map.get(self, "❓")

    @property
    def emoji(self) -> str:
        return app_emojis.get(self.value, self._fallback)
