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
from methods import groups_of_size, when


class GroupRollButton(discord.ui.Button["GroupRollContainerView"]):
    rolls_view: "GroupRollContainerView"
    lockable: bool

    def __init__(
        self,
        view: "GroupRollContainerView",
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
        row: int | None = None,
        sku_id: int | None = None,
        id: int | None = None,
    ):
        self.rolls_view = view
        self.lockable = True

        super().__init__(
            style=style,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
            sku_id=sku_id,
            id=id,
        )

    def update_locked(self, locked: bool):
        self.disabled = self.lockable and locked


class GroupRollRollButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.success, custom_id="roll_btn", label="Roll")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollRollModal(interaction, self.rolls_view))


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

        # TODO add previously stored modifier based on view.reason

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


class GroupRollSetButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.success, custom_id="set_btn", label="Set")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollSetModal(interaction, self.rolls_view))


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


class GroupRollDeleteButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.danger, custom_id="delete_btn", label="Delete Roll")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollDeleteModal(interaction, self.rolls_view))


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


class GroupRollLockButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.primary, custom_id="lock_btn", label="Lock")
        self.lockable = False

    async def callback(self, interaction: Interaction):
        await VC.play(interaction, SoundType.LOCK, True)

        if self.rolls_view.locked:
            await interaction.response.edit_message(view=self.rolls_view.unlock())
        else:
            await interaction.response.edit_message(view=self.rolls_view.lock())

    def update_locked(self, locked: bool):
        super().update_locked(locked)

        if locked:
            self.label = "Unlock"
        else:
            self.label = "Lock"


class GroupRollBulkButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.primary, custom_id="bulk_btn", label="Bulk")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollBulkModal(interaction, self.rolls_view))


class GroupRollBulkModal(BaseModal):
    modifier_input = BaseLabelTextInput(label="Creature's modifier", placeholder="0", max_length=3, required=False)
    name_input = BaseLabelTextInput(label="Creature's Name", max_length=128)
    amount_input = BaseLabelTextInput(label="Amount of creatures to add", placeholder="1 - 25", max_length=2)
    advantage_input = ModalSelectComponent(label="Roll mode", placeholder="Normal", options=Advantage.options(), required=False)
    shared_input = ModalCheckboxComponent(label="Share rolls")

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        self.view = view
        super().__init__(itr, title=f"Adding bulk {self.view.reason}!")

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


class GroupRollClearButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.danger, custom_id="Clear_btn", label="Clear Rolls")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollClearConfirmModal(interaction, self.rolls_view))


class GroupRollClearConfirmModal(BaseModal):
    confirm = ModalCheckboxComponent(label="Yes, I want to clear all rolls.")

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        self.view = view
        super().__init__(itr, title="Are you sure you want to clear?")

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


class GroupRollContainerView(ui.LayoutView):
    reason: str
    locked: bool
    rolls: dict[str, GroupRoll]
    buttons: list[GroupRollButton]
    buttons_per_row: int

    def __init__(self, reason: str):
        super().__init__(timeout=3600)

        self.reason = reason
        self.locked = False
        self.rolls = {}
        self.buttons = []
        self.buttons_per_row = 3

        self.buttons.append(GroupRollRollButton(self))
        self.buttons.append(GroupRollSetButton(self))
        self.buttons.append(GroupRollDeleteButton(self))

        self.buttons.append(GroupRollBulkButton(self))
        self.buttons.append(GroupRollLockButton(self))
        self.buttons.append(GroupRollClearButton(self))

        self.build()

    def build(self) -> "GroupRollContainerView":
        for button in self.buttons:
            button.update_locked(self.locked)

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

        button_groups = groups_of_size(self.buttons, self.buttons_per_row)
        print(button_groups)

        for group in button_groups:
            action_row = ui.ActionRow["GroupRollContainerView"](*group)
            container.add_item(action_row)

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
