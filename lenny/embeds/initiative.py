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
from logic.initiative import Initiative
from logic.roll import Advantage
from logic.voice_chat import VC, SoundType
from methods import when


class InitiativeRollModal(BaseModal):
    modifier = BaseLabelTextInput(label="Your Initiative Modifier", max_length=2, required=False)
    name = BaseLabelTextInput(label="Name", placeholder="Goblin", required=False, max_length=128)
    advantage = ModalSelectComponent(label="Roll Mode", placeholder="Normal", options=Advantage.options(), required=False)

    def __init__(self, itr: Interaction, view: "InitiativeContainerView"):
        self.name.placeholder = itr.user.display_name.title().strip()
        prev_initiative = str(DiceCache.get(itr).get_last_initiative())
        self.modifier.default = prev_initiative
        self.modifier.placeholder = prev_initiative

        super().__init__(itr, title="Rolling for Initiative")

        self.view = view

    async def on_submit(self, itr: Interaction):
        name = self.get_str(self.name)
        modifier = self.get_int(self.modifier)
        if modifier is None:
            await itr.response.send_message("Initiative Modifier must be a number without decimals.", ephemeral=True)
            return
        DiceCache.get(itr).store_initiative(modifier)

        advantage = self.get_choice(self.advantage, Advantage) or Advantage.NORMAL
        initiative = Initiative(itr, modifier, name, advantage)

        title = f"{itr.user.name} rolled Initiative for {initiative.name}{advantage.title_suffix}!"

        descriptions: list[str] = []

        for d20 in initiative.rolls:
            mod = initiative.modifier
            total = d20 + mod
            mod_str = f"+ {mod}" if mod >= 0 else f"- {-mod}"
            descriptions.append(f"- ``[{d20}] {mod_str}`` -> {total}")
        descriptions.append(f"\n**Initiative**: {initiative.get_total()}")
        description = "\n".join(descriptions)

        sound_type = SoundType.CREATURE if name else SoundType.PLAYER

        await VC.play(itr, sound_type, True)
        await itr.response.edit_message(view=self.view.add_initiative(initiative))
        await itr.followup.send(embed=UserActionEmbed(itr=itr, title=title, description=description), ephemeral=True)


class InitiativeSetModal(BaseModal):
    value = BaseLabelTextInput(label="Initiative value", max_length=3)
    name = BaseLabelTextInput(label="Name", required=False, max_length=128)

    def __init__(self, itr: Interaction, view: "InitiativeContainerView"):
        super().__init__(itr, title="Setting your Initiative value")
        self.view = view

        self.name.placeholder = itr.user.display_name.title().strip()

        for initiative in self.view.initiatives.values():
            if initiative.is_owner(itr.user) and not initiative.is_npc:
                self.value.placeholder = str(initiative.get_total())
                self.value.default = str(initiative.get_total())
                break

    async def on_submit(self, itr: Interaction):
        name = self.get_str(self.name)
        value = self.get_int(self.value)
        if not value or value < 0:
            await itr.response.send_message("Value must be a positive number without decimals.", ephemeral=True)
            return

        initiative = Initiative(itr, 0, name, Advantage.NORMAL, roll=value)

        title = f"{itr.user.name} set Initiative for {initiative.name}!"
        description = f"**Initiative**: {initiative.get_total()}"

        await VC.play(itr, SoundType.WRITE, True)
        await itr.response.edit_message(view=self.view.add_initiative(initiative))
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeDeleteModal(BaseModal):
    def __init__(self, itr: Interaction, view: "InitiativeContainerView"):
        super().__init__(itr, title="Remove initiative rolls")

        self.view = view

        checkboxes: list[ModalCheckboxGroupComponent] = [ModalCheckboxGroupComponent("Rolls to delete", options=[])]

        initiatives = list(self.view.initiatives.values())
        initiatives.sort(key=lambda init: init.name)

        for initiative in initiatives:
            if len(checkboxes[-1].options) >= 10:
                if len(checkboxes) >= 5:
                    break
                checkboxes.append(ModalCheckboxGroupComponent(label="‎ ", options=[]))

            emoji = when(initiative.is_npc, "🐉", "🧝")
            default = initiative.is_owner(itr.user) and not initiative.is_npc
            label = f"{emoji} {initiative.name}"
            checkbox_option = discord.CheckboxGroupOption(label=label, value=initiative.name, default=default)

            checkboxes[-1].options.append(checkbox_option)

        for checkbox in checkboxes:
            self.add_item(checkbox)

    async def on_submit(self, itr: Interaction) -> None:
        deleted_initiatives: list[Initiative] = []
        for child in self.children:
            group = typing.cast(ModalCheckboxGroupComponent, child)
            for name in group.values:
                initiative = self.view.initiatives[name]
                deleted_initiatives.append(initiative)

        await VC.play(itr, SoundType.DELETE, True)
        await itr.response.edit_message(view=self.view.remove_initiatives(deleted_initiatives))

        description = "\n- ".join(init.name for init in deleted_initiatives)
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

    def __init__(self, itr: Interaction, view: "InitiativeContainerView"):
        super().__init__(itr, title="Adding Initiatives in bulk!")
        self.view = view

    async def on_submit(self, itr: Interaction):
        name = str(self.name.input)
        modifier = self.get_int(self.modifier)
        amount = self.get_int(self.amount)
        advantage = self.get_choice(self.advantage, Advantage) or Advantage.NORMAL
        shared: bool = self.shared.component.value  # type: ignore

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

        initiatives = [Initiative(itr, modifier, name, advantage) for _ in range(amount)]

        if shared:
            for i in range(1, len(initiatives)):
                initiatives[i].raw_d20 = initiatives[0].raw_d20
        else:
            initiatives.sort(key=lambda init: init.get_total(), reverse=True)

        for i, initiative in enumerate(initiatives):
            initiative.name = f"{initiative.name} {i+1}"

        title = f"{itr.user.display_name} rolled Initiative for {amount} {name.strip().title()}(s)!"
        descriptions: list[str] = []
        for initiative in initiatives:
            descriptions.append(f"``{initiative.get_total():>2}`` - {initiative.name}")
        description = "\n".join(descriptions)

        await VC.play(itr, SoundType.CREATURE, True)
        await itr.response.edit_message(view=self.view.add_bulk(initiatives))
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )


class InitiativeClearConfirmModal(BaseModal):
    confirm = ModalCheckboxComponent(label="Yes, I want to clear all initiatives.")

    def __init__(self, itr: Interaction, view: "InitiativeContainerView"):
        super().__init__(itr, title="Are you sure you want to clear?")
        self.view = view

    async def on_submit(self, itr: Interaction):
        confirmed = self.confirm.value
        if not confirmed:
            await itr.response.send_message(
                embed=BaseEmbed("Clearing cancelled!", "You did not verify that you wanted to clear."),
                ephemeral=True,
            )
            return

        await VC.play(itr, SoundType.DELETE, True)
        await itr.response.edit_message(view=self.view.clear())
        await itr.followup.send(
            embed=BaseEmbed("Cleared all initiatives!", f"Cleared by {itr.user.display_name}."),
            ephemeral=True,
        )


class InitiativePlayerRow(ui.ActionRow["InitiativeContainerView"]):
    initiative_view: "InitiativeContainerView"

    def __init__(self, view: "InitiativeContainerView"):
        super().__init__()
        self.initiative_view = view

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
        delete_btn.disabled = len(self.initiative_view.initiatives) <= 0
        self.add_item(delete_btn)

    async def roll_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeRollModal(interaction, self.initiative_view))

    async def set_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeSetModal(interaction, self.initiative_view))

    async def remove_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeDeleteModal(interaction, self.initiative_view))


class InitiativeDMRow(ui.ActionRow["InitiativeContainerView"]):
    initiative_view: "InitiativeContainerView"

    def __init__(self, view: "InitiativeContainerView"):
        super().__init__()
        self.initiative_view = view

        bulk_btn = ui.Button["InitiativeContainerView"](label="Bulk", style=discord.ButtonStyle.primary, custom_id="bulk_btn")
        bulk_btn.callback = self.bulk_roll_initiative
        self.add_item(bulk_btn)

        lock_btn = ui.Button["InitiativeContainerView"](label="Lock", style=discord.ButtonStyle.primary, custom_id="lock_btn")
        lock_btn.callback = self.lock
        self.add_item(lock_btn)

        clear_btn = ui.Button["InitiativeContainerView"](
            label="Clear Rolls",
            style=discord.ButtonStyle.danger,
            custom_id="clear_btn",
        )
        clear_btn.callback = self.clear_initiative
        clear_btn.disabled = len(self.initiative_view.initiatives) <= 0
        self.add_item(clear_btn)

    async def bulk_roll_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeBulkModal(interaction, self.initiative_view))

    async def lock(self, interaction: Interaction):
        await VC.play(interaction, SoundType.LOCK, True)
        await interaction.response.edit_message(view=self.initiative_view.lock())

    async def clear_initiative(self, interaction: Interaction):
        await interaction.response.send_modal(InitiativeClearConfirmModal(interaction, self.initiative_view))


class InitiativeUnlockButton(ui.Button["InitiativeContainerView"]):
    initiative_view: "InitiativeContainerView"

    def __init__(self, view: "InitiativeContainerView"):
        super().__init__(style=discord.ButtonStyle.primary, label="Unlock", custom_id="unlock_btn")
        self.initiative_view = view

    async def callback(self, interaction: Interaction):
        await VC.play(interaction, SoundType.LOCK, True)
        await interaction.response.edit_message(view=self.initiative_view.unlock())


class InitiativeContainerView(ui.LayoutView):
    locked: bool
    initiatives: dict[str, Initiative]

    def __init__(self):
        super().__init__(timeout=3600)

        self.locked = False
        self.initiatives = dict()

        self.build()

    def build(self) -> "InitiativeContainerView":
        self.clear_items()

        container = ui.Container["InitiativeContainerView"](accent_color=discord.Color.dark_green())
        container.add_item(ui.TextDisplay("# Initiatives"))
        container.add_item(BaseSeparator())

        initiatives = list(self.initiatives.values())
        initiatives.sort(key=lambda init: (-init.get_total(), init.name, init.time_added))

        descriptions = [f"- ``{i.get_total():>2}`` - {i.name}" for i in initiatives]
        description = "\n".join(descriptions) or "*No initiatives rolled yet!*"

        container.add_item(ui.TextDisplay(description))
        container.add_item(BaseSeparator())

        if self.locked:
            unlock_section = ui.Section["InitiativeContainerView"]("‎", accessory=InitiativeUnlockButton(self))
            container.add_item(unlock_section)
        else:
            container.add_item(InitiativePlayerRow(self))
            container.add_item(InitiativeDMRow(self))

        self.add_item(container)

        return self

    def add_initiative(self, initiative: Initiative) -> "InitiativeContainerView":
        self.initiatives[initiative.name] = initiative
        return self.build()

    def remove_initiatives(self, initiatives: list[Initiative]) -> "InitiativeContainerView":
        for initiative in initiatives:
            self.initiatives.pop(initiative.name)
        return self.build()

    def add_bulk(self, initiatives: list[Initiative]) -> "InitiativeContainerView":
        for initiative in initiatives:
            self.initiatives[initiative.name] = initiative
        return self.build()

    def clear(self) -> "InitiativeContainerView":
        self.initiatives.clear()
        return self.build()

    def lock(self) -> "InitiativeContainerView":
        self.locked = True
        return self.build()

    def unlock(self) -> "InitiativeContainerView":
        self.locked = False
        return self.build()
