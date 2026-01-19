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
        super().__init__(label=tab.value, style=discord.ButtonStyle.gray, disabled=(tab == current_tab))
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

        if creature.description:
            ...

        if creature.is_summonable:
            self.container.add_item(CreatureTabActionRow(creature=creature, current_tab=tab))  # type: ignore

        match tab:
            case CreatureTab.DETAILS:
                self.add_field(name="hi", value="detail")
            case CreatureTab.TRAITS:
                self.add_field(name="hi", value="traits")
            case CreatureTab.ACTIONS:
                self.add_field(name="hi", value="actions")
            case CreatureTab.INFO:
                self.add_field(name="hi", value="info")
            case _:
                ...

        self.build()
