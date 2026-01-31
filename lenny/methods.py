from datetime import date
import logging
from enum import Enum
from typing import Any, TypeVar

import discord
import validators
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
        return [discord.app_commands.Choice(name=e.name.replace("_", " ").title(), value=e.value) for e in cls]

    @classmethod
    def options(cls) -> list[discord.SelectOption]:
        return [discord.SelectOption(label=e.value.title(), value=e.value) for e in cls]

    @classmethod
    def values(cls) -> list[Any]:
        return [e.value for e in cls]


class Boolean(ChoicedEnum):
    TRUE = "true"
    FALSE = "false"

    @property
    def bool(self) -> bool:
        return self.value == "true"


def log_button_press(itr: discord.Interaction, button: discord.ui.Button[discord.ui.LayoutView], location: str):
    logging.info("%s pressed '%s' in %s", itr.user.name, button.label, location)


def is_valid_url(url: str) -> bool:
    try:
        return bool(validators.url(url))
    except validators.utils.ValidationError:
        return False


class BotDateEvent:
    name: str
    start: tuple[int, int]
    end: tuple[int, int]
    status_message: str
    avatar_path: str

    def __init__(
        self, name: str, status_message: str, avatar_img: str, start: tuple[int, int], end: tuple[int, int] | None = None
    ):
        self.name = name
        self.status_message = status_message
        self.avatar_path = r"./assets/images/profile_pictures/" + avatar_img
        self.start = start
        self.end = end or start

    def is_active(self):
        today = date.today()
        start_date = date(today.year, *self.start)
        end_date = date(today.year, *self.end)
        return start_date <= today <= end_date
