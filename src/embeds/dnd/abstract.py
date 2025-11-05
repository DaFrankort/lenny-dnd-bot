import logging
import discord
from logic.dnd.abstract import DNDEntry, Description
from methods import build_table

HORIZONTAL_LINE = "~~-------------------------------------------------------------------------------------~~"


class DNDEntryEmbed(discord.Embed):
    """
    Superclass for DNDObjects that helps ensure data stays within Discord's character limits.
    Additionally provides functions to handle Description-field & Table generation.
    """

    _entry: DNDEntry
    view: discord.ui.View | None = None
    file: discord.File | None = None

    def __init__(self, entry: DNDEntry):
        self._entry = entry

        super().__init__(
            title=entry.title,
            type="rich",
            color=discord.Color.dark_green(),
            url=entry.url,
        )

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

    def build_table(self, value, CHAR_FIELD_LIMIT=1024):
        """Turns a Description with headers & rows into a clean table using rich."""
        table_string = build_table(value)

        if len(table_string) > CHAR_FIELD_LIMIT:
            return f"The table for [{self._entry.name} can be found here]({self._entry.url})."
        return table_string

    def add_description_fields(
        self,
        descriptions: list[Description],
        ignore_tables=False,
        CHAR_FIELD_LIMIT=1024,
        CHAR_EMBED_LIMIT=6000,
        MAX_FIELDS=25,
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

        CHAR_FIELD_LIMIT = min(CHAR_FIELD_LIMIT, 1024)
        CHAR_EMBED_LIMIT = min(CHAR_EMBED_LIMIT, 6000)
        MAX_FIELDS = min(MAX_FIELDS, 25)

        char_count = self.char_count
        for description in descriptions:
            if (len(self.fields)) >= MAX_FIELDS:
                logging.debug(
                    f"{self._entry.entry_type.upper()} - Max field count reached! {len(self.fields)} >= {MAX_FIELDS}"
                )
                break

            name = description["name"]
            value = description["value"]
            type = description["type"]

            if type == "table":
                if ignore_tables:
                    continue
                value = self.build_table(value, CHAR_FIELD_LIMIT)

            field_length = len(name) + len(value)
            if field_length >= CHAR_FIELD_LIMIT:
                logging.debug(
                    f"{self._entry.entry_type.upper()} - Field character limit reached! {field_length} >= {CHAR_FIELD_LIMIT}"
                )
                continue  # TODO split field to fit, possibly concatenate descriptions to make optimal use of field-limits

            char_count += field_length
            if char_count >= CHAR_EMBED_LIMIT:
                logging.debug(
                    f"{self._entry.entry_type.upper()} - Embed character limit reached! {char_count} >= {CHAR_EMBED_LIMIT}"
                )
                break  # TODO Cut description short and add a message

            self.add_field(name=name, value=value, inline=False)
