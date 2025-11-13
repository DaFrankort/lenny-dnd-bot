from typing import Optional

import discord
import discord.ui

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


class LabeledTextComponent(discord.ui.Label[discord.ui.LayoutView]):
    def __init__(
        self,
        *,
        label: str,
        style: discord.TextStyle = discord.TextStyle.short,
        placeholder: Optional[str] = None,
        required: bool = True,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> None:
        super().__init__(
            text=label,
            component=discord.ui.TextInput[discord.ui.LayoutView](
                style=style,
                placeholder=placeholder,
                required=required,
                min_length=min_length,
                max_length=max_length,
            ),
        )

    @property
    def input(self) -> discord.ui.TextInput[discord.ui.LayoutView]:
        if isinstance(self.component, discord.ui.TextInput):
            return self.component
        raise ValueError("SimpleTextInput component is not a discord.ui.TextInput!")
