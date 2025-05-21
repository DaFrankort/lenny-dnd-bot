import logging
import re
import discord

from dnd import DNDObject, Item, Spell, Condition

HORIZONTAL_LINE = "~~-------------------------------------------------------------------------------------~~"


class MultiDNDSelect(discord.ui.Select):
    name: str
    query: str
    entries: list[DNDObject]
    embed: any

    def __init__(self, query: str, entries: list[DNDObject], name: str, embed: any):
        self.name = name
        self.query = query
        self.entries = entries
        self.embed = embed

        options = []
        for entry in entries:
            options.append(self.select_option(entry))

        super().__init__(
            placeholder=f"Results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

        logging.debug(f"{name}: found {len(entries)} spells for '{query}'")

    def select_option(self, entry: DNDObject) -> discord.SelectOption:
        return discord.SelectOption(label=f"{entry.name} ({entry.source})")

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
        await interaction.response.send_message(embed=self.embed(entry))


class SpellEmbed(discord.Embed):
    """A class representing a Discord embed for a Dungeons & Dragons spell."""

    def __init__(self, spell: Spell):
        title = f"{spell.name} ({spell.source})"
        classes = spell.get_formatted_classes()

        super().__init__(
            title=title,
            type="rich",
            color=discord.Color.dark_green(),
            url=spell.url,
        )
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
            for description in spell.description:
                self.add_field(
                    name=description["name"], value=description["text"], inline=False
                )


class MultiSpellSelect(MultiDNDSelect):
    """A class representing a Discord select menu for multiple spell selection."""

    query: str
    spells: list[Spell]

    def __init__(self, query: str, spells: list[Spell]):
        super().__init__(query, spells, "MultiSpellSelect", SpellEmbed)

    def select_option(self, entry: Spell) -> discord.SelectOption:
        return discord.SelectOption(
            label=f"{entry.name} ({entry.source})",
            description=f"{entry.level} {entry.school}",
        )


class MultiSpellSelectView(discord.ui.View):
    """A class representing a Discord view for multiple spell selection."""

    def __init__(self, query: str, spells: list[Spell]):
        super().__init__()
        self.add_item(MultiSpellSelect(query, spells))


class ItemEmbed(discord.Embed):
    def __init__(self, item: Item) -> None:
        title = f"{item.name} ({item.source})"
        super().__init__(
            title=title,
            type="rich",
            color=discord.Color.dark_green(),
            url=item.url,
        )

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
                self.add_field(name=desc["name"], value=desc["text"], inline=False)


class MultiItemSelect(MultiDNDSelect):
    def __init__(self, query: str, entries: list[Item]):
        super().__init__(query, entries, "MultiItemSelect", ItemEmbed)


class MultiItemSelectView(discord.ui.View):
    def __init__(self, query: str, items: list[Item]):
        super().__init__()
        self.add_item(MultiItemSelect(query, items))


class ConditionEmbed(discord.Embed):
    def __init__(self, condition: Condition):
        title = f"{condition.name} ({condition.source})"

        super().__init__(
            title=title,
            type="rich",
            color=discord.Color.dark_green(),
            url=condition.url,
        )
        if len(condition.description) == 0:
            return

        self.description = condition.description[0]["text"]
        for description in condition.description[1:]:
            self.add_field(
                name=description["name"], value=description["text"], inline=False
            )

        if condition.image:
            self.set_thumbnail(url=condition.image)


class MultiConditionSelect(MultiDNDSelect):
    def __init__(self, query: str, entries: list[Condition]):
        super().__init__(query, entries, "MultiConditionSelect", ConditionEmbed)


class MultiConditionSelectView(discord.ui.View):
    def __init__(self, query: str, conditions: list[Condition]):
        super().__init__()
        self.add_item(MultiConditionSelect(query, conditions))


class SimpleEmbed(discord.Embed):
    def __init__(
        self, title: str | None, description: str | None, color: discord.Color = None
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
        title_fail: str | None,
        description: str | None,
        success: bool,
    ):
        title_fail = title_fail or title_success
        title = title_success if success else title_fail
        color = discord.Color.dark_green() if success else discord.Color.red()
        super().__init__(title, description, color)


class NoSearchResultsFoundEmbed(SimpleEmbed):
    def __init__(self, query: str):
        super().__init__("No results found.", f"No results found for '{query}'.")


class NoSpellsFoundEmbed(SimpleEmbed):
    def __init__(self, query: str):
        super().__init__("No spells found.", f"No spells found for '{query}'.")


class NoItemsFoundEmbed(SimpleEmbed):
    def __init__(self, query: str):
        super().__init__("No items found.", f"No items found for '{query}'.")


class NoConditionsFoundEmbed(SimpleEmbed):
    def __init__(self, query: str):
        super().__init__("No conditions found.", f"No conditions found for '{query}'.")
