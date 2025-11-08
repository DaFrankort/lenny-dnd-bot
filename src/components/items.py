import discord
from methods import when


class TitleTextDisplay(discord.ui.TextDisplay[discord.ui.LayoutView]):
    """A TextDisplay which is formatted as a title, with optional source and URL."""

    def __init__(self, name: str, source: str | None = None, url: str | None = None, id: int | None = None):
        title = when(source, f"{name} ({source})", name)
        title = when(url, f"[{title}]({url})", title)
        title = f"### {title}"
        super().__init__(content=title, id=id)


class SimpleSeparator(discord.ui.Separator[discord.ui.LayoutView]):
    def __init__(self, is_large: bool = False):
        if is_large:
            super().__init__(spacing=discord.SeparatorSpacing.large)
        else:
            super().__init__(spacing=discord.SeparatorSpacing.small)
