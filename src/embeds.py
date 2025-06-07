import io
import logging
import re
import discord
import rich
from dnd import Class, Creature, DNDObject, Description, Item, Spell, Condition
from user_colors import UserColor
from rich.table import Table
from rich.console import Console

HORIZONTAL_LINE = "~~-------------------------------------------------------------------------------------~~"


class MultiDNDSelect(discord.ui.Select):
    name: str
    query: str
    entries: list[DNDObject]

    def __init__(self, query: str, entries: list[DNDObject]):
        self.name = entries[0].__class__.__name__.upper() if entries else "UNKNOWN"
        self.query = query
        self.entries = entries

        options = []
        for entry in entries:
            options.append(self.select_option(entry))

        super().__init__(
            placeholder=f"Results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

        logging.debug(f"{self.name}: found {len(entries)} entries for '{query}'")

    def select_option(self, entry: DNDObject) -> discord.SelectOption:
        return discord.SelectOption(
            label=f"{entry.name} ({entry.source})", description=entry.select_description
        )

    async def callback(self, interaction: discord.Interaction):
        """Handles the selection of a spell from the select menu."""
        full_name = self.values[0]
        name_pattern = r"^(.+) \(([^\)]+)\)"  # "Name (Source)"
        name_match = re.match(name_pattern, full_name)
        name = name_match.group(1)
        source = name_match.group(2)

        entry = [
            entry
            for entry in self.entries
            if entry.name == name and entry.source == source
        ][0]
        logging.debug(
            f"{self.name}: user {interaction.user.display_name} selected '{name}"
        )
        await interaction.response.send_message(embed=entry.get_embed())


class MultiDNDSelectView(discord.ui.View):
    """A class representing a Discord view for multiple DNDObject selection."""

    def __init__(self, query: str, entries: list[DNDObject]):
        super().__init__()
        self.add_item(MultiDNDSelect(query, entries))


class _DNDObjectEmbed(discord.Embed):
    """
    Superclass for DNDObjects that helps ensure data stays within Discord's character limits.
    Additionally provides functions to handle Description-field & Table generation.
    """

    _object: DNDObject

    def __init__(self, object: DNDObject):
        self._object = object

        super().__init__(
            title=object.title,
            type="rich",
            color=discord.Color.dark_green(),
            url=object.url,
        )

    @property
    def char_count(self):
        """The total amount of characters currently in the embed."""

        char_count = (
            (len(self.title) if self.title else 0)
            + (len(self.description) if self.description else 0)
            + (len(self.footer.text) if self.footer and self.footer.text else 0)
            + (len(self.author.name) if self.author else 0)
        )

        if self.fields:
            for field in self.fields:
                char_count += len(field.name) + len(field.value)

        return char_count

    def build_table(self, value, CHAR_FIELD_LIMIT=1024):
        """Turns a Description with headers & rows into a clean table using rich."""

        headers = value["headers"]
        rows = value["rows"]
        table = Table(style=None, box=rich.box.ROUNDED)

        for header in headers:
            table.add_column(header, justify="left", style=None)

        for row in rows:
            row = map(str, row)
            table.add_row(*row)

        buffer = io.StringIO()
        console = Console(file=buffer, width=56)
        console.print(table)
        table_string = f"```{buffer.getvalue()}```"
        buffer.close()

        if len(table_string) > CHAR_FIELD_LIMIT:
            return f"The table for [{self._object.name} can be found here]({self._object.url})."
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
                    f"{self._object.object_type.upper()} - Max field count reached! {len(self.fields)} >= {MAX_FIELDS}"
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
                    f"{self._object.object_type.upper()} - Field character limit reached! {field_length} >= {CHAR_FIELD_LIMIT}"
                )
                continue  # TODO split field to fit, possibly concatenate descriptions to make optimal use of field-limits

            char_count += field_length
            if char_count >= CHAR_EMBED_LIMIT:
                logging.debug(
                    f"{self._object.object_type.upper()} - Embed character limit reached! {char_count} >= {CHAR_EMBED_LIMIT}"
                )
                break  # TODO Cut description short and add a message

            self.add_field(name=name, value=value, inline=False)


class SpellEmbed(_DNDObjectEmbed):
    """A class representing a Discord embed for a Dungeons & Dragons spell."""

    def __init__(self, spell: Spell):
        classes = spell.get_formatted_classes()

        super().__init__(spell)

        self.add_field(name="Type", value=spell.level_school, inline=True)
        self.add_field(name="Casting Time", value=spell.casting_time, inline=True)
        self.add_field(name="Range", value=spell.spell_range, inline=True)
        self.add_field(name="Components", value=spell.components, inline=True)
        self.add_field(name="Duration", value=spell.duration, inline=True)
        self.add_field(name="Classes", value=classes, inline=True)

        if len(spell.description) > 0:
            # Add horizontal line
            self.add_field(
                name="",
                value=HORIZONTAL_LINE,
                inline=False,
            )
            self.add_description_fields(spell.description)


class ItemEmbed(_DNDObjectEmbed):
    def __init__(self, item: Item) -> None:
        super().__init__(item)

        value_weight = item.formatted_value_weight
        properties = item.formatted_properties
        type = item.formatted_type
        descriptions = item.description

        if type is not None:
            self.add_field(name="", value=f"*{type}*", inline=False)

        if properties is not None:
            self.add_field(name="", value=properties, inline=False)

        if value_weight is not None:
            self.add_field(name="", value=value_weight, inline=False)

        if len(descriptions) > 0:
            # Add horizontal line
            self.add_field(
                name="",
                value=HORIZONTAL_LINE,
                inline=False,
            )

            for desc in item.description:
                self.add_field(
                    name=desc["name"], value=desc["text"], inline=False
                )  # TODO items.json does not follow the Description convention yet. ('text' instead of 'value')


class ConditionEmbed(_DNDObjectEmbed):
    def __init__(self, condition: Condition):
        super().__init__(condition)

        if len(condition.description) == 0:
            return

        self.description = condition.description[0]["value"]
        self.add_description_fields(condition.description[1:])

        if condition.image:
            self.set_thumbnail(url=condition.image)


class CreatureEmbed(_DNDObjectEmbed):
    def __init__(self, creature: Creature):
        super().__init__(creature)
        self.description = creature.subtitle

        if creature.token_url:
            self.set_thumbnail(url=creature.token_url)

        if creature.summoned_by_spell:
            self.add_field(name="Summoned by:", value=creature.summoned_by_spell)

        self.add_description_fields(
            creature.description, ignore_tables=True, MAX_FIELDS=3
        )


class ClassEmbed(_DNDObjectEmbed):
    def __init__(self, character_class: Class, page: int = 0, subclass: str | None = None):
        page = max(0, min(20, page))

        super().__init__(character_class)

        if page == 0:
            self.description = "Core Info"
            self.add_description_fields(character_class.base_info)
            return

        subtitle = f"Level {page}"
        if subclass and page <= (character_class.subclass_unlock_level or 0):
            subtitle += f" | {subclass}"
        self.description = subtitle

        # Level Resources are handled differently, since we want inline fields here.
        level_resources = character_class.level_resources.get(page, [])
        for resource in level_resources:
            name = resource["name"]
            if resource["type"] == "table":
                value = self.build_table(resource["value"])
                inline = False
            else:
                value = resource["value"]
                inline = True

            self.add_field(name=name, value=value, inline=inline)

        # Rest of the descriptions
        descriptions = character_class.level_features.get(page, []).copy()
        if subclass:
            descriptions += character_class.subclass_level_features.get(subclass, {}).get(page, [])
        self.add_description_fields(descriptions=descriptions)


class SimpleEmbed(discord.Embed):
    def __init__(
        self, title: str, description: str, color: discord.Color = None
    ) -> None:
        if not color:
            color = discord.Color.dark_green()

        super().__init__(
            color=color,
            title=title,
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        ),

        if description:
            self.add_field(name="", value=description)


class SuccessEmbed(SimpleEmbed):
    """A class based on SimpleEmbed which easily toggles the color from green to red."""

    def __init__(
        self,
        title_success: str,
        title_fail: str,
        description: str | None,
        success: bool,
    ):
        title = title_success if success else title_fail
        color = discord.Color.dark_green() if success else discord.Color.red()
        super().__init__(title, description, color)


class UserActionEmbed(SimpleEmbed):
    """A class based on SimpleEmbed which sets the author to the user who triggered the action."""

    def __init__(self, itr: discord.Interaction, title: str, description: str):
        super().__init__(
            "",
            description,
            color=UserColor.get(itr),
        ),
        self.set_author(
            name=title,
            icon_url=itr.user.display_avatar.url,
        )


class NoResultsFoundEmbed(SimpleEmbed):
    def __init__(self, name: str, query: str):
        super().__init__(
            f"No {name} found.",
            f"No results found for '{query}'.",
            color=discord.Color.red(),
        )
