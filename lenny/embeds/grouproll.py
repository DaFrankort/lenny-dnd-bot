from typing import Sequence
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
from logic.grouproll import GroupRoll, GroupRollRoll, GroupRollSet
from logic.roll import Advantage
from logic.voice_chat import VC, SoundType
from methods import when


class GroupRollRollModal(BaseModal):
    view: "GroupRollContainerView"
    reason: str
    name_input: BaseLabelTextInput
    modifier_input: BaseLabelTextInput
    advantage_input: ModalSelectComponent

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        super().__init__(itr, title=f"Rolling for {view.reason}")

        self.view = view
        display_name = itr.user.display_name.title().strip()

        self.name_input = BaseLabelTextInput(
            label="Name",
            placeholder=display_name,
            required=False,
            max_length=128,
        )
        self.modifier_input = BaseLabelTextInput(
            label="Your modifier",
            max_length=32,
            required=False,
        )
        self.advantage_input = ModalSelectComponent(
            label="Roll mode",
            placeholder="Normal",
            options=Advantage.options(),
            required=False,
        )

        self.add_item(self.modifier_input)
        self.add_item(self.name_input)
        self.add_item(self.advantage_input)

    async def on_submit(self, itr: Interaction):
        name = self.name or ""
        modifier = self.modifier or "0"
        advantage = self.advantage or Advantage.NORMAL

        group_roll = GroupRollRoll(itr, name, modifier, advantage)

        title = f"{itr.user.name} rolled {self.view.reason} for {group_roll.name}{advantage.title_suffix}!"
        descriptions: list[str] = []

        for roll in group_roll.roll.result.rolls:
            descriptions.append(f"- ``{roll.expr}`` -> {roll.total}")
        descriptions.append(f"\n**{self.view.reason.title()}**: {group_roll.total}")
        description = "\n".join(descriptions)

        await VC.play(itr, self.sound, True)
        await itr.response.edit_message(view=self.view.add_roll(group_roll))
        await itr.followup.send(embed=UserActionEmbed(itr=itr, title=title, description=description), ephemeral=True)

    @property
    def name(self) -> str | None:
        return self.get_str(self.name_input)

    @property
    def modifier(self) -> str | None:
        return self.get_str(self.modifier_input)

    @property
    def advantage(self) -> Advantage | None:
        return self.get_choice(self.advantage_input, Advantage)

    @property
    def sound(self) -> SoundType:
        # Specific use case for initiatives
        if self.view.reason == "initiative":
            return SoundType.CREATURE if self.name else SoundType.PLAYER
        return SoundType.ROLL


class GroupRollSetModal(BaseModal):
    name_input: BaseLabelTextInput
    value_input: BaseLabelTextInput

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        super().__init__(itr, title=f"Setting your {self.view.reason} value")

        self.view = view
        display_name = itr.user.display_name.title().strip()

        self.name_input = BaseLabelTextInput(label=display_name, required=False, max_length=128)
        self.value_input = BaseLabelTextInput(label="Value", max_length=3)

        for roll in self.view.rolls.values():
            if roll.is_owner(itr.user) and not roll.is_npc:
                self.value_input.default = str(roll.total)
                self.value_input.placeholder = str(roll.total)
                break

    async def on_submit(self, itr: Interaction):
        if not self.value or self.value < 0:
            await itr.response.send_message("Value must be a positive number without decimals.", ephemeral=True)
            return

        group_roll = GroupRollSet(itr, self.name, self.value)

        title = f"{itr.user.name} set {self.view.reason} for {group_roll.name}!"
        description = f"**{self.view.reason.title()}**: {group_roll.total}"

        await VC.play(itr, SoundType.WRITE, True)
        await itr.response.edit_message(view=self.view.add_roll(group_roll))
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )

    @property
    def name(self) -> str | None:
        return self.get_str(self.name_input)

    @property
    def value(self) -> int | None:
        return self.get_int(self.value_input)


class GroupRollDeleteModal(BaseModal):
    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        self.view = view

        super().__init__(itr, title=f"Remove {self.view.reason} rolls")
        checkboxes: list[ModalCheckboxGroupComponent] = [ModalCheckboxGroupComponent("Rolls to delete", options=[])]

        rolls = list(self.view.rolls.values())
        rolls.sort(key=lambda init: init.name)

        for roll in rolls:
            if len(checkboxes[-1].options) >= 10:
                if len(checkboxes) >= 5:
                    break
                checkboxes.append(ModalCheckboxGroupComponent(label="‎ ", options=[]))

            emoji = when(roll.is_npc, "🐉", "🧝")
            default = roll.is_owner(itr.user) and not roll.is_npc
            label = f"{emoji} {roll.name}"
            checkbox_option = discord.CheckboxGroupOption(label=label, value=roll.name, default=default)

            checkboxes[-1].options.append(checkbox_option)

        for checkbox in checkboxes:
            self.add_item(checkbox)

    async def on_submit(self, itr: Interaction) -> None:
        removed: list[GroupRoll] = []
        for child in self.children:
            group = typing.cast(ModalCheckboxGroupComponent, child)
            for name in group.values:
                roll = self.view.rolls[name]
                removed.append(roll)

        description = "\n- ".join(roll.name for roll in removed)
        embed = BaseEmbed(title=f"Removed {self.view.reason}", description=f"- {description}")

        await VC.play(itr, SoundType.DELETE, True)
        await itr.response.edit_message(view=self.view.remove_rolls(removed))
        await itr.followup.send(embed=embed, ephemeral=True)


class GroupRollBulkModal(BaseModal):
    modifier_input = BaseLabelTextInput(label="Creature's modifier", placeholder="0", max_length=3, required=False)
    name_input = BaseLabelTextInput(label="Creature's Name", max_length=128)
    amount_input = BaseLabelTextInput(label="Amount of creatures to add", placeholder="1 - 25", max_length=2)
    advantage_input = ModalSelectComponent(label="Roll mode", placeholder="Normal", options=Advantage.options(), required=False)
    shared_input = ModalCheckboxComponent(label="Share rolls")

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        super().__init__(itr, title=f"Adding bulk {self.view.reason}!")
        self.view = view

    async def on_submit(self, itr: Interaction):
        if self.modifier is None or self.amount is None:
            await itr.response.send_message("Modifier and amount must be a number without a decimals.", ephemeral=True)
            return

        if self.amount <= 0:
            await itr.response.send_message("Amount must be a numerical value larger than 0.", ephemeral=True)
            return

        name = self.name
        amount = self.amount
        shared = self.shared
        modifier = self.modifier
        advantage = self.advantage or Advantage.NORMAL

        rolls = [GroupRollRoll(itr, name, modifier, advantage) for _ in range(amount)]

        if shared:
            for i in range(1, len(rolls)):
                rolls[i].roll = rolls[0].roll
        else:
            rolls.sort(key=lambda init: init.total, reverse=True)

        for i, roll in enumerate(rolls):
            roll.name = f"{roll.name} {i + 1}"

        title = f"{itr.user.display_name} rolled {self.view.reason} for {amount} {name.strip().title()}(s)!"
        descriptions: list[str] = []
        for roll in rolls:
            descriptions.append(f"``{roll.total:>2}`` - {roll.name}")
        description = "\n".join(descriptions)

        await VC.play(itr, SoundType.CREATURE, True)
        await itr.response.edit_message(view=self.view.add_bulk(rolls))
        await itr.followup.send(
            embed=UserActionEmbed(itr=itr, title=title, description=description),
            ephemeral=True,
        )

    @property
    def name(self) -> str:
        return str(self.name_input.input)

    @property
    def modifier(self) -> str | None:
        return self.get_str(self.modifier_input)

    @property
    def amount(self) -> int | None:
        return self.get_int(self.amount_input)

    @property
    def advantage(self) -> Advantage | None:
        return self.get_choice(self.advantage_input, Advantage)

    @property
    def shared(self) -> bool:
        return self.shared.component.value  # type: ignore


class GroupRollClearConfirmModal(BaseModal):
    confirm = ModalCheckboxComponent(label="Yes, I want to clear all rolls.")

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
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
            embed=BaseEmbed("Cleared all rolls!", f"Cleared by {itr.user.display_name}."),
            ephemeral=True,
        )


class GroupRollPlayerRow(ui.ActionRow["GroupRollContainerView"]):
    rolls_view: "GroupRollContainerView"

    def __init__(self, view: "GroupRollContainerView"):
        super().__init__()
        self.rolls_view = view

        roll_btn = ui.Button["GroupRollContainerView"](style=discord.ButtonStyle.success, custom_id="roll_btn", label="Roll")
        roll_btn.callback = self.roll_grouproll
        self.add_item(roll_btn)

        set_btn = ui.Button["GroupRollContainerView"](style=discord.ButtonStyle.success, custom_id="set_btn", label="Set")
        set_btn.callback = self.set_grouproll
        self.add_item(set_btn)

        delete_btn = ui.Button["GroupRollContainerView"](
            style=discord.ButtonStyle.danger, custom_id="delete_btn", label="Delete Roll"
        )
        delete_btn.callback = self.remove_grouproll
        delete_btn.disabled = len(self.rolls_view.rolls) <= 0
        self.add_item(delete_btn)

    async def roll_grouproll(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollRollModal(interaction, self.rolls_view))

    async def set_grouproll(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollSetModal(interaction, self.rolls_view))

    async def remove_grouproll(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollDeleteModal(interaction, self.rolls_view))


class GroupRollDMRow(ui.ActionRow["GroupRollContainerView"]):
    roll_view: "GroupRollContainerView"

    def __init__(self, view: "GroupRollContainerView"):
        super().__init__()
        self.roll_view = view

        bulk_btn = ui.Button["GroupRollContainerView"](label="Bulk", style=discord.ButtonStyle.primary, custom_id="bulk_btn")
        bulk_btn.callback = self.bulk_roll_grouproll
        self.add_item(bulk_btn)

        lock_btn = ui.Button["GroupRollContainerView"](label="Lock", style=discord.ButtonStyle.primary, custom_id="lock_btn")
        lock_btn.callback = self.lock
        self.add_item(lock_btn)

        clear_btn = ui.Button["GroupRollContainerView"](
            label="Clear Rolls",
            style=discord.ButtonStyle.danger,
            custom_id="clear_btn",
        )
        clear_btn.callback = self.clear_grouproll
        clear_btn.disabled = len(self.roll_view.rolls) <= 0
        self.add_item(clear_btn)

    async def bulk_roll_grouproll(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollBulkModal(interaction, self.roll_view))

    async def lock(self, interaction: Interaction):
        await VC.play(interaction, SoundType.LOCK, True)
        await interaction.response.edit_message(view=self.roll_view.lock())

    async def clear_grouproll(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollClearConfirmModal(interaction, self.roll_view))


class GroupRollUnlockButton(ui.Button["GroupRollContainerView"]):
    roll_view: "GroupRollContainerView"

    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(style=discord.ButtonStyle.primary, label="Unlock", custom_id="unlock_btn")
        self.roll_view = view

    async def callback(self, interaction: Interaction):
        await VC.play(interaction, SoundType.LOCK, True)
        await interaction.response.edit_message(view=self.roll_view.unlock())


class GroupRollContainerView(ui.LayoutView):
    reason: str
    locked: bool
    rolls: dict[str, GroupRoll]

    def __init__(self, reason: str):
        super().__init__(timeout=3600)

        self.reason = reason
        self.locked = False
        self.rolls = {}

        self.build()

    def build(self) -> "GroupRollContainerView":
        self.clear_items()

        container = ui.Container["GroupRollContainerView"](accent_color=discord.Color.dark_green())
        container.add_item(ui.TextDisplay(f"# {self.reason.title()}"))
        container.add_item(BaseSeparator())

        rolls = list(self.rolls.values())
        rolls.sort(key=lambda roll: (-roll.total, roll.name, roll.time_added))

        descriptions = [f"- ``{roll.total:>2}`` - {roll.name}" for roll in rolls]
        description = "\n".join(descriptions) or "*No dice rolled yet!*"

        container.add_item(ui.TextDisplay(description))
        container.add_item(BaseSeparator())

        if self.locked:
            unlock_section = ui.Section["GroupRollContainerView"]("‎", accessory=GroupRollUnlockButton(self))
            container.add_item(unlock_section)
        else:
            container.add_item(GroupRollPlayerRow(self))
            container.add_item(GroupRollDMRow(self))

        self.add_item(container)

        return self

    def add_roll(self, roll: GroupRoll) -> "GroupRollContainerView":
        self.rolls[roll.name] = roll
        return self.build()

    def remove_rolls(self, rolls: Sequence[GroupRoll]) -> "GroupRollContainerView":
        for roll in rolls:
            self.rolls.pop(roll.name)
        return self.build()

    def add_bulk(self, rolls: Sequence[GroupRoll]) -> "GroupRollContainerView":
        for roll in rolls:
            self.rolls[roll.name] = roll
        return self.build()

    def clear(self) -> "GroupRollContainerView":
        self.rolls.clear()
        return self.build()

    def lock(self) -> "GroupRollContainerView":
        self.locked = True
        return self.build()

    def unlock(self) -> "GroupRollContainerView":
        self.locked = False
        return self.build()
