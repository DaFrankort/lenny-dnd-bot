from enum import Enum

import discord

from embeds import SimpleEmbed
from localisation import FieldInfo, LocalisationBank


class HelpTabs(Enum):
    Default = "General"
    Roll = "Rolling Dice"
    Initiative = "Initiative Tracking"
    DND = "D&D Info Lookup"
    TokenGen = "Token Generation"
    Color = "User Color"
    Stats = "Character Stats"


def _format_command_list_item(description: str) -> str:
    """Formats a text to be displayed with a bullet point in the help embed."""
    return f"- ``/{description}``" if description else ""


def _get_default_help_inline_fields() -> list[FieldInfo]:
    """
    Returns a list of FieldInfo with each command per category, to be rendered with inline = True.
    This is only displayed on the general help tab.
    """
    fields = [
        FieldInfo(
            name=HelpTabs.Roll.value,
            description=[
                "roll",
                "advantage",
                "disadvantage",
                "d20",
            ],
        ),
        FieldInfo(
            name=HelpTabs.Initiative.value,
            description=[
                "initiative",
                "bulkinitiative",
                "setinitiative",
                "swapinitiative",
                "removeinitiative",
                "showinitiative",
                "clearinitiative",
            ],
        ),
        FieldInfo(
            name=HelpTabs.DND.value,
            description=[
                "spell",
                "item",
                "condition",
                "creature",
                "feat",
                "rule",
                "action",
                "search",
            ],
        ),
        FieldInfo(
            name=HelpTabs.TokenGen.value,
            description=[
                "tokengen",
                "tokengenurl",
            ],
        ),
        FieldInfo(
            name=HelpTabs.Color.value,
            description=[
                "color",
            ],
        ),
        FieldInfo(
            name=HelpTabs.Stats.value,
            description=[
                "stats",
            ],
        ),
    ]

    for field in fields:
        field._descriptions = [
            _format_command_list_item(d) for d in field._descriptions if d
        ]

    return sorted(fields, key=lambda f: len(f._descriptions), reverse=True)


class HelpTabSelect(discord.ui.Select):
    """A select menu to choose a help tab."""

    def __init__(self):
        options = [
            discord.SelectOption(label=tab.value, value=tab.name) for tab in HelpTabs
        ]
        super().__init__(placeholder="Select a help tab", options=options)

    async def callback(self, interaction: discord.Interaction):
        """Updates the help embed based on the selected tab."""
        selected_tab = HelpTabs[self.values[0]]
        embed = get_help_embed(selected_tab)
        await interaction.response.edit_message(embed=embed)


class HelpTabView(discord.ui.View):
    """A view that contains the help tab select menu."""

    def __init__(self):
        super().__init__()
        self.add_item(HelpTabSelect())


def get_help_embed(tab: HelpTabs) -> SimpleEmbed:
    """Generates a help embed depending on the selected tab."""
    embed = SimpleEmbed(
        title=f"Help - {tab.value}",
        description="",
    )

    if tab == HelpTabs.Default:
        embed.description = LocalisationBank.get_default_help_text()
        for info in _get_default_help_inline_fields():
            embed.add_field(name=info.name, value=info.description, inline=True)

    else:
        field_info = LocalisationBank.get_help_info(tab.name)
        for info in field_info:
            embed.add_field(name=info.name, value=info.description, inline=False)

    return embed
