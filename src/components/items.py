from discord import ui
import discord
from methods import when


class TitleTextDisplay(ui.TextDisplay):
    """A TextDisplay which is formatted as a title, with optional source and URL."""

    def __init__(self, name: str, source: str = None, url: str = None, id=None):
        title = when(source, f"{name} ({source})", name)
        title = when(url, f"[{title}]({url})", title)
        title = f"### {title}"
        super().__init__(content=title, id=id)


class SimpleSeparator(ui.Separator):
    def __init__(self, is_large=False):
        if is_large:
            super().__init__(spacing=discord.SeparatorSpacing.large)
        else:
            super().__init__(spacing=discord.SeparatorSpacing.small)
