import io
import logging
import discord
import rich
from dnd import (
    Background,
    Class,
    Creature,
    DNDObject,
    DNDTable,
    Description,
    Feat,
    Item,
    Language,
    Rule,
    Spell,
    Condition,
)
from user_colors import UserColor
from rich.table import Table
from rich.console import Console

from voice_chat import VC, SoundType

HORIZONTAL_LINE = "~~-------------------------------------------------------------------------------------~~"


def log_button_press(
    itr: discord.Interaction, button: discord.ui.Button, location: str
):
    logging.info(f"{itr.user.name} pressed '{button.label}' in {location}")


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
        index = self.entries.index(entry)
        return discord.SelectOption(
            label=f"{entry.name} ({entry.source})",
            description=entry.select_description,
            value=str(index),
        )

    async def callback(self, interaction: discord.Interaction):
        """Handles the selection of a spell from the select menu."""
        index = int(self.values[0])
        entry = self.entries[index]

        logging.debug(
            f"{self.name}: user {interaction.user.display_name} selected option {index}: '{entry.name}`"
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
    view: discord.ui.View = None

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
            formatted_row = [
                cell.notation if hasattr(cell, "notation") else str(cell)
                for cell in row
            ]
            table.add_row(*formatted_row)

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

        self._set_embed_color(spell)
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

    def _set_embed_color(self, spell: Spell):
        school_colors = {
            "abjuration": discord.Colour.from_rgb(0, 185, 33),
            "conjuration": discord.Colour.from_rgb(189, 0, 68),
            "divination": discord.Colour.from_rgb(0, 173, 179),
            "enchantment": discord.Colour.from_rgb(179, 0, 131),
            "evocation": discord.Colour.from_rgb(172, 1, 9),
            "illusion": discord.Colour.from_rgb(14, 109, 174),
            "necromancy": discord.Colour.from_rgb(108, 24, 141),
            "transmutation": discord.Colour.from_rgb(204, 190, 0),
        }

        school = spell.school.lower()
        self.color = school_colors.get(school, discord.Colour.green())


class ItemEmbed(_DNDObjectEmbed):
    def __init__(self, item: Item) -> None:
        super().__init__(item)

        value_weight = item.formatted_value_weight
        properties = item.formatted_properties
        type = item.formatted_type
        descriptions = item.description

        if type is not None:
            self._set_embed_color(item)
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

            self.add_description_fields(item.description)

    def _set_embed_color(self, item: Item):
        type_colors = {
            "common": discord.Colour.green(),
            "uncommon": discord.Colour.from_rgb(178, 114, 63),
            "rare": discord.Colour.from_rgb(166, 155, 190),
            "very rare": discord.Colour.from_rgb(208, 172, 63),
            "legendary": discord.Colour.from_rgb(140, 194, 216),
            "artifact": discord.Colour.from_rgb(200, 37, 35),
            "varies": discord.Colour.from_rgb(186, 187, 187),
            "unknown": discord.Colour.from_rgb(186, 187, 187),
        }

        color = None
        for type in item.type:
            cleaned_type = type.split("(")[0].strip().lower()
            if cleaned_type in type_colors:
                color = type_colors[cleaned_type]
                break

        self.color = color or discord.Colour.from_rgb(149, 149, 149)


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

        if creature.description:
            self.add_description_fields(
                creature.description, ignore_tables=True, MAX_FIELDS=3
            )


class MultiClassSubclassSelect(discord.ui.Select):
    """Select component to provide a Subclass-dropdown under a ClassEmbed"""

    def __init__(
        self,
        character_class: Class,
        get_level: callable,
        subclass: str,
        parent_view: "ClassNavigationView",
    ):
        options = []
        for subclass_name in character_class.subclass_level_features.keys():
            if not character_class.is_phb2014 and subclass_name.endswith("(PHB)"):
                continue  # Only show PHB subclasses for PHB classes

            label = (
                subclass_name
                if subclass != subclass_name
                else f"{subclass_name} [Current]"
            )
            options.append(discord.SelectOption(label=label, value=subclass_name))

        super().__init__(
            placeholder="Select Subclass", min_values=1, max_values=1, options=options
        )

        self.character_class = character_class
        self.get_level = get_level
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        subclass = self.values[0]
        self.parent_view.subclass = subclass
        level = self.get_level()
        embed = ClassEmbed(self.character_class, level, subclass)
        await interaction.response.edit_message(embed=embed, view=embed.view)


class MultiClassPageSelect(discord.ui.Select):
    """Select component to quickly navigate between class-pages (base info or level info)"""

    def __init__(
        self,
        character_class: Class,
        get_subclass: callable,
        page: int,
        parent_view: "ClassNavigationView",
    ):
        options = []
        core_label = "Core Info" if page != 0 else "Core Info [Current]"
        options.append(discord.SelectOption(label=core_label, value="0"))
        for level in character_class.level_resources.keys():
            label = (
                f"Level {level}" if int(level) != page else f"Level {level} [Current]"
            )
            options.append(discord.SelectOption(label=label, value=level))

        super().__init__(
            placeholder="Select Level", min_values=1, max_values=1, options=options
        )

        self.character_class = character_class
        self.get_subclass = get_subclass
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        level = int(self.values[0])
        self.parent_view.level = level
        subclass = self.get_subclass()
        embed = ClassEmbed(self.character_class, level, subclass)
        await interaction.response.edit_message(embed=embed, view=embed.view)


class ClassNavigationView(discord.ui.View):
    level: int
    subclass: str | None

    def __init__(self, character_class: Class, level: int, subclass: str | None):
        super().__init__()

        self.character_class = character_class
        self.level = level
        self.subclass = subclass

        if character_class.level_resources:
            self.add_item(
                MultiClassPageSelect(
                    self.character_class, lambda: self.subclass, self.level, self
                )
            )
        if character_class.subclass_level_features:
            self.add_item(
                MultiClassSubclassSelect(
                    self.character_class, lambda: self.level, self.subclass, self
                )
            )


class ClassEmbed(_DNDObjectEmbed):
    def __init__(
        self, character_class: Class, level: int = 0, subclass: str | None = None
    ):
        level = max(0, min(20, level))

        super().__init__(character_class)

        if level == 0:  # Core Info (page 0)
            self.description = "*Core Info*"

            if character_class.primary_ability:
                self.add_field(
                    name="Primary Ability",
                    value=character_class.primary_ability,
                    inline=True,
                )
            if character_class.spellcast_ability:
                self.add_field(
                    name="Spellcast Ability",
                    value=character_class.spellcast_ability,
                    inline=True,
                )

            self.add_description_fields(character_class.base_info)

        else:
            subtitle = f"Level {level}"
            if subclass and level >= (character_class.subclass_unlock_level or 0):
                subtitle += f" {subclass}"
            self.description = f"*{subtitle}*"

            # Level Resources are handled differently, since we want inline fields here.
            level_resources = character_class.level_resources.get(str(level), [])
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
            descriptions = character_class.level_features.get(str(level), []).copy()
            if subclass:
                subclass_level_descriptions = (
                    character_class.subclass_level_features.get(subclass, {})
                )
                subclass_description = subclass_level_descriptions.get(
                    str(level), []
                ).copy()
                descriptions.extend(subclass_description)

            if descriptions:
                self.add_field(name="", value=HORIZONTAL_LINE, inline=False)
                self.add_description_fields(descriptions=descriptions)

        self.set_footer(text=f"Page {level + 1} / 21", icon_url="")
        self.view = ClassNavigationView(character_class, level, subclass)


class RuleEmbed(_DNDObjectEmbed):
    def __init__(self, rule: Rule):
        super().__init__(rule)
        self.description = f"*{rule.select_description}*"
        self.add_description_fields(rule.description)


class ActionEmbed(_DNDObjectEmbed):
    def __init__(self, rule: Rule):
        super().__init__(rule)
        self.description = f"*{rule.select_description}*"
        self.add_description_fields(rule.description)


class FeatEmbed(_DNDObjectEmbed):
    def __init__(self, feat: Feat):
        super().__init__(feat)
        self.description = f"*{feat.select_description}*"

        if feat.ability_increase:
            self.add_field(
                name="Ability Increase", value=feat.ability_increase, inline=True
            )
        if feat.prerequisite:
            self.add_field(name="Requires", value=feat.prerequisite, inline=True)
        if feat.ability_increase or feat.prerequisite:
            self.add_field(name="", value=HORIZONTAL_LINE, inline=False)

        self.add_description_fields(feat.description)


class LanguageEmbed(_DNDObjectEmbed):
    def __init__(self, language: Language):
        super().__init__(language)
        self.description = f"*{language.select_description}*"

        if language.speakers:
            self.add_field(
                name="Typical Speakers", value=language.speakers, inline=True
            )
        if language.script:
            self.add_field(name="Script", value=language.script, inline=True)

        if language.description:
            if len(self.fields) > 0:
                self.add_field(name="", value=HORIZONTAL_LINE, inline=False)
            self.add_description_fields(language.description)


class BackgroundEmbed(_DNDObjectEmbed):
    def __init__(self, background: Background):
        super().__init__(background)
        if background.description:
            self.add_description_fields(background.description)


class TableView(discord.ui.View):
    table: DNDTable

    def __init__(self, table: DNDTable):
        super().__init__()
        self.table = table

    @discord.ui.button(
        label="Roll", style=discord.ButtonStyle.primary, custom_id="roll_btn"
    )
    async def add(self, itr: discord.Interaction, btn: discord.ui.Button):
        row, expression = self.table.roll()
        print(row, expression)
        if row is None or expression is None:
            # Disable button to prevent further attempts, since it will keep failing.
            btn.disabled = True
            btn.style = discord.ButtonStyle.gray
            await itr.response.send_message(
                "❌ Couldn't roll table, something went wrong. ❌"
            )
            await itr.message.edit(view=self)
            return

        console_table = Table(style=None, box=rich.box.ROUNDED)
        # Omit the first header and first row value
        for header in self.table.table["value"]["headers"][1:]:
            console_table.add_column(header, justify="left", style=None)
        console_table.add_row(*row[1:])

        buffer = io.StringIO()
        console = Console(file=buffer, width=56)
        console.print(console_table)
        description = f"```{buffer.getvalue()}```"
        buffer.close()

        embed = UserActionEmbed(
            itr=itr, title=expression.title, description=description
        )
        embed.title = f"{self.table.name} [{expression.roll.value}]"
        await itr.response.send_message(embed=embed)
        await VC.play(itr, sound_type=SoundType.ROLL)


class TableEmbed(_DNDObjectEmbed):
    def __init__(self, table: DNDTable):
        super().__init__(table)
        if table.table:
            self.description = self.build_table(table.table["value"], CHAR_FIELD_LIMIT=4000)

        if table.footnotes:
            footnotes = "\n".join(table.footnotes)
            if len(table.footnotes) == 1:
                self.set_footer(text=footnotes.replace("*", ""), icon_url=None)
            else:
                desc = Description(name="", type="text", value=f"*{footnotes}*")
                self.add_description_fields([desc])

        if table.is_rollable:
            self.view = TableView(table)


class SimpleEmbed(discord.Embed):
    def __init__(
        self, title: str, description: str | None, color: discord.Color = None
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
