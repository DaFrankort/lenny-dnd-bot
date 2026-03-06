import typing

import discord
from discord import Interaction, ui

from embeds.components import (
    BaseLabelTextInput,
    BaseModal,
    BaseSeparator,
    ModalCheckboxComponent,
    ModalCheckboxGroupComponent,
    ModalSelectComponent,
)
from embeds.embed import BaseEmbed, UserActionEmbed
from logic.dicecache import DiceCache
from logic.initiative import Initiative, Initiatives
from logic.roll import Advantage
from logic.voice_chat import VC, SoundType
from methods import when


class InitiativeRollModal(BaseModal):
    modifier = BaseLabelTextInput(label="Your Initiative Modifier", max_length=2, required=False)
    name = BaseLabelTextInput(label="Name", placeholder="Goblin", required=False, max_length=128)
    advantage = ModalSelectComponent(label="Roll Mode", placeholder="Normal", options=Advantage.options(), required=False)

    def __init__(self, itr: Interaction):
        self.name.input.placeholder = itr.user.display_name.title().strip()
        prev_initiative = str(DiceCache.get(itr).get_last_initiative())
        self.modifier.input.default = prev_initiative
        self.modifier.input.placeholder = prev_initiative
        super().__init__(itr, title="Rolling for Initiative")

    async def on_submit(self, itr: Interaction):
        name = self.get_str(self.name)
        modifier = self.get_int(self.modifier)
        if modifier is None:
            await itr.response.send_message("Initiative Modifier must be a number without decimals.", ephemeral=True)
            return
        DiceCache.get(itr).store_initiative(modifier)

        advantage = self.get_choice(self.advantage, Advantage) or Advantage.NORMAL
        initiative = Initiative(itr, modifier, name, advantage)
        Initiatives.add(itr, initiative)

        title = f"{itr.user.name} rolled Initiative for {initiative.name}{advantage.title_suffix}!"

        descriptions: list[str] = []

        for d20 in initiative.rolls:
            mod = initiative.modifier
            total = d20 + mod
            mod_str = f"+ {mod}" if mod >= 0 else f"- {-mod}"
            descriptions.append(f"- ``[{d20}] {mod_str}`` -> {total}")
        descriptions.append(f"\n**Initiative**: {initiative.get_total()}")
        description = "\n".join(descriptions)

        view = InitiativeContainerView(itr)
        sound_type = SoundType.CREATURE if name else SoundType.PLAYER
        await itr.response.defer()
        await VC.play(itr, sound_type, True)
        if itr.message:
            await itr.followup.edit_message(message_id=itr.message.id, view=view)
            await itr.followup.send(
                embed=UserActionEmbed(itr=itr, title=title, description=description),
                ephemeral=True,
            )


class InitiativeSetModal(BaseModal):
    value = BaseLabelTextInput(label="Initiative value", max_length=3)
    name = BaseLabelTextInput(label="Name", required=False, max_length=128)

    def __init__(self, itr: Interaction):
        super().__init__(itr, title="Setting your Initiative value")

        self.name.input.placeholder = itr.user.display_name.title().strip()
        for initiative in Initiatives.get(itr):
            if initiative.is_owner(itr.user) and not initiative.is_npc:
                self.value.component.placeholder = str(initiative.get_total())  # type: ignore
                self.value.component.default = str(initiative.get_total())  # type: ignore
                break

    async def on_submit(self, itr: Interaction):
        name = self.get_str(self.name)
        value = self.get_int(self.value)
        if not value or value < 0:
            await itr.response.send_message("Value must be a positive number without decimals.", ephemeral=True)
            return

        initiative = Initiative(itr, 0, name, Advantage.NORMAL, roll=value)
        Initiatives.add(itr, initiative)

        title = f"{itr.user.name} set Initiative for {initiative.name}!"
        description = f"**Initiative**: {initiative.get_total()}"

        view = InitiativeContainerView(itr)
        await VC.play(itr, SoundType.WRITE, True)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeDeleteModal(BaseModal):
    def __init__(self, itr: Interaction):
        super().__init__(itr, title="Remove initiative rolls")

        checkboxes: list[ModalCheckboxGroupComponent] = [ModalCheckboxGroupComponent("Rolls to delete", options=[])]
        for initiative in Initiatives.get(itr):
            if len(checkboxes[-1].component.options) >= 10:  # type: ignore
                if len(checkboxes) >= 5:
                    break
                checkboxes.append(ModalCheckboxGroupComponent(label="‎ ", options=[]))

            emoji = when(initiative.is_npc, "🐉", "🧝")
            default = initiative.is_owner(itr.user) and not initiative.is_npc
            label = f"{emoji} {initiative.name}"
            checkbox_option = discord.CheckboxGroupOption(label=label, value=initiative.name, default=default)

            checkboxes[-1].component.options.append(checkbox_option)  # type: ignore

        for checkbox in checkboxes:
            self.add_item(checkbox)

    async def on_submit(self, itr: Interaction) -> None:
        deleted_initiatives: list[str] = []
        for child in self.children:
            child = typing.cast(ModalCheckboxGroupComponent, child)
            for name in child.values:
                initiative = Initiatives.remove(itr, name)
                deleted_initiatives.append(initiative.name)

        view = InitiativeContainerView(itr)

        await VC.play(itr, SoundType.DELETE, True)
        await itr.response.edit_message(view=view)

        description = "\n- ".join(deleted_initiatives)
        embed = BaseEmbed(title="Removed initiative", description=f"- {description}")
        await itr.followup.send(embed=embed, ephemeral=True)


class InitiativeBulkModal(BaseModal):
    modifier = BaseLabelTextInput(
        label="Creature's Initiative Modifier",
        placeholder="0",
        max_length=3,
        required=False,
    )
    name = BaseLabelTextInput(label="Creature's Name", max_length=128)
    amount = BaseLabelTextInput(label="Amount of creatures to add", placeholder="1 - 25", max_length=2)
    advantage = ModalSelectComponent(label="Roll Mode", placeholder="Normal", options=Advantage.options(), required=False)
    shared = ModalCheckboxComponent(label="Share Initiative")

    def __init__(self, itr: Interaction):
        super().__init__(itr, title="Adding Initiatives in bulk!")

    async def on_submit(self, itr: Interaction):
        name = str(self.name.input)
        modifier = self.get_int(self.modifier)
        amount = self.get_int(self.amount)

        if modifier is None or amount is None:
            await itr.response.send_message(
                "Modifier and Amount must be a number without a decimals.",
                ephemeral=True,
            )
            return
        if amount <= 0:
            await itr.response.send_message(
                "Amount must be a numerical value larger than 0.",
                ephemeral=True,
            )
            return

        advantage = self.get_choice(self.advantage, Advantage) or Advantage.NORMAL
        shared: bool = self.shared.component.value  # type: ignore
        initiatives = Initiatives.add_bulk(itr, modifier, name, amount, advantage, shared)  # type: ignore

        title = f"{itr.user.display_name} rolled Initiative for {amount} {name.strip().title()}(s)!"
        descriptions: list[str] = []
        for initiative in initiatives:
            descriptions.append(f"``{initiative.get_total():>2}`` - {initiative.name}")
        description = "\n".join(descriptions)

        view = InitiativeContainerView(itr)
        await VC.play(itr, SoundType.CREATURE, True)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeClearConfirmModal(BaseModal):
    confirm = ModalCheckboxComponent(label="Yes, I want to clear all initiatives.")

    def __init__(self, itr: Interaction):
        super().__init__(itr, title="Are you sure you want to clear?")

    async def on_submit(self, itr: Interaction):
        confirmed = self.confirm.value
        if not confirmed:
            await itr.response.send_message(
                embed=BaseEmbed("Clearing cancelled!", "You did not verify that you wanted to clear."),
                ephemeral=True,
            )
            return

        Initiatives.clear(itr)
        view = InitiativeContainerView(itr)
        await VC.play(itr, SoundType.DELETE, True)
        await itr.response.edit_message(view=view)
        await itr.followup.send(
            embed=BaseEmbed("Cleared all initiatives!", f"Cleared by {itr.user.display_name}."),
            ephemeral=True,
        )


class InitiativePlayerRow(ui.ActionRow["InitiativeContainerView"]):
    def __init__(self, itr: discord.Interaction):
        super().__init__()

        roll_btn = ui.Button["InitiativeContainerView"](style=discord.ButtonStyle.success, custom_id="roll_btn", label="Roll")
        roll_btn.callback = self.roll_initiative
        self.add_item(roll_btn)

        set_btn = ui.Button["InitiativeContainerView"](style=discord.ButtonStyle.success, custom_id="set_btn", label="Set")
        set_btn.callback = self.set_initiative
        self.add_item(set_btn)

        delete_btn = ui.Button["InitiativeContainerView"](
            style=discord.ButtonStyle.danger, custom_id="delete_btn", label="Delete Roll"
        )
        delete_btn.callback = self.remove_initiative
        delete_btn.disabled = len(Initiatives.get(itr)) <= 0
        self.add_item(delete_btn)

    async def roll_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeRollModal(interaction))

    async def set_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeSetModal(interaction))

    async def remove_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeDeleteModal(interaction))


class InitiativeDMRow(ui.ActionRow["InitiativeContainerView"]):
    @ui.button(label="Bulk", style=discord.ButtonStyle.primary, custom_id="bulk_btn", row=1)
    async def bulk_roll_initiative(
        self, itr: Interaction, button: ui.Button["InitiativeContainerView"]
    ):  # pylint: disable=unused-argument
        await itr.response.send_modal(InitiativeBulkModal(itr))

    @ui.button(label="Lock", style=discord.ButtonStyle.primary, custom_id="lock_btn", row=1)
    async def lock(self, itr: Interaction, button: ui.Button["InitiativeContainerView"]):  # pylint: disable=unused-argument
        await VC.play(itr, SoundType.LOCK, True)
        await itr.response.edit_message(view=InitiativeContainerView(itr, True))

    @ui.button(
        label="Clear Rolls",
        style=discord.ButtonStyle.danger,
        custom_id="clear_btn",
        row=1,
    )
    async def clear_initiative(
        self, itr: Interaction, button: ui.Button["InitiativeContainerView"]
    ):  # pylint: disable=unused-argument
        await itr.response.send_modal(InitiativeClearConfirmModal(itr))


class InitiativeUnlockButton(ui.Button["InitiativeContainerView"]):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.primary, label="Unlock", custom_id="unlock_btn")

    async def callback(self, interaction: Interaction):
        await VC.play(interaction, SoundType.LOCK, True)
        await interaction.response.edit_message(view=InitiativeContainerView(interaction, False))


class InitiativeContainerView(ui.LayoutView):
    def __init__(self, itr: Interaction, locked: bool = False):
        super().__init__(timeout=None)

        container = ui.Container["InitiativeContainerView"](accent_color=discord.Color.dark_green())
        container.add_item(ui.TextDisplay("# Initiatives"))
        container.add_item(BaseSeparator())

        initiatives = Initiatives.get(itr)
        descriptions = [f"- ``{i.get_total():>2}`` - {i.name}" for i in initiatives]
        description = "\n".join(descriptions) or "*No initiatives rolled yet!*"

        container.add_item(ui.TextDisplay(description))
        container.add_item(BaseSeparator())

        if locked:
            unlock_section = ui.Section["InitiativeContainerView"]("‎", accessory=InitiativeUnlockButton())
            container.add_item(unlock_section)
        else:
            container.add_item(InitiativePlayerRow(itr))
            container.add_item(InitiativeDMRow())

        self.add_item(container)
