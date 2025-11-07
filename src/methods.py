import dataclasses
from enum import Enum
import logging
import re
from typing import TypeVar, Any
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
        logging.warning(f"Font '{font}' could not be loaded!")
        return ImageFont.load_default(size=size)


class ChoicedEnum(Enum):
    @classmethod
    def choices(cls) -> list[discord.app_commands.Choice[str]]:
        return [discord.app_commands.Choice(name=e.name.title(), value=e.value) for e in cls]

    @classmethod
    def values(cls) -> list[Any]:
        return [e.value for e in cls]


def _format_md_to_discord(text: str) -> str:
    while "####" in text:
        text = text.replace("####", "###")  # unsupported header formats: ### is max header
    text = re.sub(r"\[\[(.*?)\]\]", r"\1", text)  # Obsidian file links: [[FILE]]
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)  # Reference links: [FILENAME][FILEPATH]
    return text


@dataclasses.dataclass
class MDFile:
    title: str
    content: str

    @classmethod
    async def from_attachment(cls, file: discord.Attachment):
        if not file.content_type:
            raise ValueError("Attached file has unknown filetype.")
        if "text/markdown" not in file.content_type:
            raise ValueError("Attached file must be a .md file.")

        file_bytes = await file.read()
        title = file.filename.replace(".md", "").replace("_", " ")
        content = file_bytes.decode("utf-8")
        content = _format_md_to_discord(content)
        return cls(title, content)
