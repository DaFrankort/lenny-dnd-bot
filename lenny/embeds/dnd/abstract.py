import logging

import discord

from logic.dnd.abstract import Description, DescriptionTableTable, DNDEntry, build_table

HORIZONTAL_LINE = "~~-------------------------------------------------------------------------------------~~"
HORIZONTAL_LINE_SHORT = "~~------------------------------------------------------------------~~"


class DNDEntryEmbed(discord.Embed):
    """
    Superclass for DNDEntries that helps ensure data stays within Discord's character limits.
    Additionally provides functions to handle Description-field & Table generation.
    """

    _entry: DNDEntry
    view: discord.ui.View | None = None
    file: discord.File | None = None

    def __init__(self, entry: DNDEntry, thumbnail_url: str | None = None):
        self._entry = entry

        super().__init__(
            title=entry.title,
            type="rich",
            color=discord.Color.dark_green(),
            url=entry.url,
        )

        if thumbnail_url:
            self.set_thumbnail(url=thumbnail_url)

    @property
    def char_count(self):
        """The total amount of characters currently in the embed."""

        char_count = (
            (len(self.title) if self.title else 0)
            + (len(self.description) if self.description else 0)
            + (len(self.footer.text) if self.footer and self.footer.text else 0)
            + (len(self.author.name) if self.author.name else 0)
        )

        if self.fields:
            for field in self.fields:
                field_name_len = len(field.name) if field.name else 0
                field_value_len = len(field.value) if field.value else 0
                char_count += field_name_len + field_value_len

        return char_count

    def build_table(self, value: str | DescriptionTableTable, char_field_limit: int = 1024):
        """Turns a Description with headers & rows into a clean table using rich."""
        table_string = build_table(value)

        if len(table_string) > char_field_limit:
            return f"The table for [{self._entry.name} can be found here]({self._entry.url})."
        return table_string

    def add_description_fields(
        self,
        descriptions: list[Description],
        ignore_tables: bool = False,
        char_field_limit: int = 1024,
        char_embed_limit: int = 6000,
        max_fields: int = 25,
    ):
        """
        Adds fields to the embed for each Description in the list.
        Ensures that neither the number of fields nor the total character count exceeds Discord's embed limits.

        Discord embed limits:
        - Title: 256 characters
        - Description: 4096 characters
        - Fields: Up to 25 fields
            - Field name: 256 characters
            - Field value: 1024 characters
        - Footer: 2048 characters
        - Author name: 256 characters
        - Embed total size (including all fields, title, description, footer, etc.): 6000 characters
        """

        char_field_limit = min(char_field_limit, 1024)
        char_embed_limit = min(char_embed_limit, 6000)
        max_fields = min(max_fields, 25)

        char_count = self.char_count
        entry_type = self._entry.entry_type
        for description in descriptions:
            if (len(self.fields)) >= max_fields:
                logging.debug("%s - Max field count reached! %d >= %d", entry_type.upper(), len(self.fields), max_fields)
                break

            name = description["name"]

            if description["type"] == "text":
                value = description["value"]
            elif description["type"] == "table":
                if ignore_tables:
                    value = ""
                else:
                    value = self.build_table(description["table"], char_field_limit)
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

            self.add_field(name=name, value=value, inline=False)

    def add_separator_field(self):
        """
        Adds a separator line with adjusted width if there is a thumbnail image present.
        A thumbnail should be set **before** using this method.
        """
        line = HORIZONTAL_LINE
        if self.thumbnail.url:
            line = HORIZONTAL_LINE_SHORT
        self.add_field(name="", value=line, inline=False)
