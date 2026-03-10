import logging
from typing import Any

import discord

from components.items import TitleTextDisplay
from embeds.dnd.abstract import build_list
from logic.color import UserColor
from logic.dnd.abstract import Description, DNDEntry, build_table


class BaseEmbed(discord.Embed):
    def __init__(self, title: str, description: str | None, color: discord.Color | None = None) -> None:
        color = color or discord.Color.dark_green()

        super().__init__(color=color, title=title, type="rich", url=None, description=None, timestamp=None)

        if description:
            self.add_field(name="", value=description, inline=False)


class SuccessEmbed(BaseEmbed):
    """A class based on BaseEmbed to easily toggle the color from green to red."""

    def __init__(self, title_success: str, title_fail: str, description: str | None, success: bool):
        title = title_success if success else title_fail
        color = discord.Color.dark_green() if success else discord.Color.red()
        super().__init__(title, description, color)


class UserActionEmbed(BaseEmbed):
    """A class based on BaseEmbed which sets the author to the user who triggered the action."""

    def __init__(self, itr: discord.Interaction, title: str, description: str):
        super().__init__("", description, color=discord.Color(UserColor.get(itr)))
        self.set_author(name=title, icon_url=itr.user.display_avatar.url)


class NoResultsFoundEmbed(BaseEmbed):
    def __init__(self, name: str, query: str):
        super().__init__(f"No {name} found.", f"No results found for '{query}'.", color=discord.Color.red())


class ErrorEmbed(BaseEmbed):
    def __init__(self, error: str):
        super().__init__("Error!", f"{error}", color=discord.Color.red())


class BaseLayoutView(discord.ui.LayoutView):
    container: discord.ui.Container[Any]
    file: discord.File | None = None

    def __init__(
        self,
        title: str,
        url: str | None = None,
        thumbnail_img: str | None = None,
        color: discord.Color = discord.Color.dark_green(),
        spoiler: bool = False,
        timeout: int = 180,
    ):
        super().__init__(timeout=timeout)
        self.container = discord.ui.Container(accent_color=color, spoiler=spoiler)

        title_item = TitleTextDisplay(title, None, url)
        if thumbnail_img:
            thumbnail_item = discord.ui.Thumbnail(thumbnail_img)  # type: ignore
            header = discord.ui.Section(title_item, accessory=thumbnail_item)  # type: ignore
            self.container.add_item(header)
        else:
            self.container.add_item(title_item)

    def set_thumbnail_image(self, img_url: str):
        self.thumbnail = img_url

    def add_field(self, name: str | None, value: str):
        text = f"**{name}**\n{value}" if name else value
        self.container.add_item(discord.ui.TextDisplay(text))

    def build(self):
        self.add_item(self.container)

    def add_description_fields(
        self,
        entry: DNDEntry,
        descriptions: list[Description],
        ignore_tables: bool = False,
        char_field_limit: int = 1024,
        char_embed_limit: int = 6000,
        max_components: int = 25,
    ):
        char_field_limit = min(char_field_limit, 1024)
        char_embed_limit = min(char_embed_limit, 6000)
        max_components = min(max_components, 25)

        char_count = 5000  # TODO
        entry_type = entry.entry_type
        for description in descriptions:
            if (len(self.container.children)) >= max_components:
                logging.debug(
                    "%s - Max component count reached! %d >= %d", entry_type, len(self.container.children), max_components
                )
                break

            name = description["name"]

            if description["type"] == "text":
                value = description["value"]
            elif description["type"] == "table":
                if ignore_tables:
                    value = ""
                else:
                    value = build_table(description["table"])
            elif description["type"] == "list":
                value = build_list(entry, description["list"], char_field_limit)
            else:
                value = ""

            field_length = len(name) + len(value)
            if field_length >= char_field_limit:
                logging.debug(
                    "%s - Field character limit reached! %d >= %d", entry_type.upper(), field_length, char_field_limit
                )
                continue  # TODO split field to fit, possibly concatenate descriptions to make optimal use of field-limits

            char_count += field_length
            if char_count >= char_embed_limit:
                logging.debug("%s - Embed character limit reached! %d >= %d", entry_type.upper(), char_count, char_embed_limit)
                break  # TODO Cut description short and add a message

            self.add_field(name=name, value=value)
