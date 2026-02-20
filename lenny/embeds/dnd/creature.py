import discord

from embeds.embed import BaseLayoutView
from logic.dnd.creature import Creature
from methods import ChoicedEnum


class CreatureTab(ChoicedEnum):
    DEFAULT = "Base"
    DETAILS = "Details"
    TRAITS = "Traits"
    ACTIONS = "Actions"
    INFO = "Info"


class CreatureTabButton(discord.ui.Button):  # type: ignore
    def __init__(self, creature: Creature, tab: CreatureTab, current_tab: CreatureTab):
        selected = tab == current_tab
        style = discord.ButtonStyle.gray if not selected else discord.ButtonStyle.blurple
        super().__init__(label=tab.value, style=style, disabled=selected)
        self.creature = creature
        self.tab = tab

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=CreatureLayoutView(self.creature, self.tab))


class CreatureTabActionRow(discord.ui.ActionRow):  # type: ignore
    def __init__(self, creature: Creature, current_tab: CreatureTab):
        super().__init__()  # type: ignore
        self.creature = creature
        self.current_tab = current_tab

        for tab in CreatureTab:
            if tab is CreatureTab.DEFAULT:
                continue

            if tab is CreatureTab.DETAILS and (not creature.details and not creature.stats):
                continue

            if tab is CreatureTab.TRAITS and not creature.traits:
                continue

            if tab is CreatureTab.ACTIONS and (not creature.actions and not creature.bonus_actions):
                continue

            if tab is CreatureTab.INFO and not creature.description:
                continue

            self.add_item(CreatureTabButton(creature=creature, tab=tab, current_tab=current_tab))


class CreatureLayoutView(BaseLayoutView):
    def __init__(self, creature: Creature, tab: CreatureTab = CreatureTab.DEFAULT):
        super().__init__(
            title=creature.title, url=creature.url, thumbnail_img=creature.token_url, spoiler=creature.is_summonable
        )

        if creature.summoned_by_spell:
            self.add_field(name="Summoned by spell", value=creature.summoned_by_spell)
        if creature.summoned_by_class:
            self.add_field(name="Summoned by class", value=creature.summoned_by_class)

        if creature.is_summonable:
            self.container.add_item(CreatureTabActionRow(creature=creature, current_tab=tab))  # type: ignore

        match tab:
            case CreatureTab.DETAILS:
                self.add_description_fields(creature, creature.stats)
                self.add_description_fields(creature, creature.details)

            case CreatureTab.TRAITS:
                self.add_description_fields(creature, creature.traits)

            case CreatureTab.ACTIONS:
                self.add_description_fields(creature, creature.actions)

            case CreatureTab.INFO:
                self.add_description_fields(creature, creature.description)

            case _:
                ...

        self.build()
