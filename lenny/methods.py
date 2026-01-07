import logging
from enum import Enum
from typing import Any, TypeVar
from urllib.parse import urlparse

import discord
from PIL import ImageFont
import requests

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


def log_button_press(itr: discord.Interaction, button: discord.ui.Button[discord.ui.LayoutView], location: str):
    logging.info("%s pressed '%s' in %s", itr.user.name, button.label, location)


def is_valid_url(url: str, verify_accessible: bool) -> bool:
    """
    Checks if the given URL is syntactically valid. If verify_accessible is True, also checks if the URL is reachable (HTTP 200 response).
    Args:
        url (str): The URL string to validate.
        verify_accessible (bool): If True, perform a HEAD request to check if the URL is reachable.
    Returns:
        bool: True if the URL is valid (and reachable if verify_accessible is True), False otherwise.
    """
    parsed_url = urlparse(url)
    # Check for valid scheme and network location
    if not (parsed_url.scheme in ("http", "https") and parsed_url.netloc):
        return False
    if not verify_accessible:
        return True

    try:
        head_response = requests.head(url, allow_redirects=False)
        return head_response.status_code == 200
    except requests.RequestException:
        return False
