import logging
from enum import Enum
from typing import Any, TypeVar

import discord
from PIL import ImageFont

T = TypeVar("T")
U = TypeVar("U")


def when(condition: bool | str | int | None, value_on_true: T, value_on_false: U) -> T | U:
    """Wrapper method for a ternary statement, for readability"""
    return value_on_true if condition else value_on_false


class FontType(str, Enum):
    MONOSPACE = "./assets/fonts/GoogleSansCode-Light.ttf"
    FANTASY = "./assets/fonts/Merienda-Light.ttf"


def get_font(font: FontType, size: float):
    try:
        return ImageFont.truetype(font=font, size=size)
    except OSError:
        logging.warning("Font '%s' could not be loaded!", font)
        return ImageFont.load_default(size=size)


class ChoicedEnum(Enum):
    @classmethod
    def choices(cls) -> list[discord.app_commands.Choice[str]]:
        return [discord.app_commands.Choice(name=e.name.title(), value=e.value) for e in cls]

    @classmethod
    def options(cls) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=e.name.title(), value=e.value) for e in cls]

    @classmethod
    def values(cls) -> list[Any]:
        return [e.value for e in cls]


class Boolean(ChoicedEnum):
    TRUE = "true"
    FALSE = "false"

    @property
    def bool(self) -> bool:
        return self.value == "true"
