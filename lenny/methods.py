import json
import logging
import os
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

import discord
import thread
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


def is_valid_url(url: str) -> bool:
    try:
        return bool(validators.url(url))
    except validators.utils.ValidationError:
        return False


def call_with_timeout(timeout: int, func: Callable[..., T], args: list[Any]) -> T | None:
    proc = thread.Thread(target=func, args=args)
    proc.start()
    proc.join(timeout=timeout)

    if proc.is_alive():
        proc.kill()
        return None

    return proc.result


def join_strings(strings: list[str], separator: str, final_separator: str) -> str:
    """
    Join multiple strings together with a special final separator. For example:
    join_strings(["a", "b", "c"], ",", ", and")  -> "a, b, and c"
    """
    if len(strings) == 0:
        return ""

    if len(strings) == 1:
        return strings[0]

    first_strings = strings[:-1]
    last_string = strings[-1]
    first_part = separator.join(first_strings)

    return final_separator.join([first_part, last_string])


def read_dnd_data_contents(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"D&D data file not found: '{path}'")
    if not os.path.isfile(path):
        raise TypeError(f"D&D data file is not a file: '{path}'")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
