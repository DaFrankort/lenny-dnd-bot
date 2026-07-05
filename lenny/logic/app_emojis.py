import logging
from enum import Enum
from pathlib import Path

import discord

EMOJI_DIR = Path("./assets/images/emojis")
APP_EMOJIS: dict[str, str] = {}


def format_emoji_name(path: Path) -> str:
    relative_path = path.relative_to(EMOJI_DIR)
    parts = list(relative_path.parent.parts) + [relative_path.stem]
    full_name = "_".join(parts).strip().lower().replace(" ", "_")
    return full_name


def get_emoji_files() -> list[tuple[str, Path]]:
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}
    files = [file for file in EMOJI_DIR.rglob("*") if file.is_file() and file.suffix.lower() in valid_extensions]
    return [(format_emoji_name(file), file) for file in files]


def init_app_emojis(emojis: list[discord.Emoji]):
    APP_EMOJIS.clear()
    APP_EMOJIS.update({emoji.name: str(emoji) for emoji in emojis})


# pylint: disable=duplicate-code
class AppEmoji(Enum):
    # ENTRY TYPES
    # NOTE: Does not have custom emojis yet.
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
    ARTIFICER = "class_artificer"
    BARBARIAN = "class_barbarian"
    BARD = "class_bard"
    CLERIC = "class_cleric"
    DRUID = "class_druid"
    FIGHTER = "class_fighter"
    MONK = "class_monk"
    PALADIN = "class_paladin"
    RANGER = "class_ranger"
    ROGUE = "class_rogue"
    SORCERER = "class_sorcerer"
    WARLOCK = "class_warlock"
    WIZARD = "class_wizard"

    # Species
    AASIMAR = "species_aasimar"
    DWARF = "species_dwarf"
    HUMAN = "species_human"

    # Background
    ARTIST = "background_artist"
    ACOLYTE = "background_acolyte"

    @property
    def _fallback(self) -> str:
        fallback_map = {
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
            # SPECIES
            self.AASIMAR: "👼",
            self.DWARF: "🧔",
            self.HUMAN: "👱",
            # BACKGROUND
            self.ARTIST: "👨‍🎨",
            self.ACOLYTE: "👨‍🎓",
        }
        logging.warning("Using fallback emoji for '%s'", self.value)
        return fallback_map.get(self, "❓")

    @property
    def emoji(self) -> str:
        return APP_EMOJIS.get(self.value) or self._fallback  # Use of 'or' to prevent _fallback log messages.
