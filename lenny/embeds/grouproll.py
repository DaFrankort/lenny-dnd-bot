import typing
from typing import Sequence

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
from logic.grouproll import GroupRoll, GroupRollRoll, GroupRollSet
from logic.roll import Advantage
from logic.voice_chat import VC, SoundType
from methods import groups_of_size, when


class GroupRollModal(BaseModal):
    view: "GroupRollContainerView"

    def __init__(self, itr: Interaction[discord.Client], title: str, view: "GroupRollContainerView"):
        self.view = view
        super().__init__(itr, title)


class GroupRollButton(discord.ui.Button["GroupRollContainerView"]):
    rolls_view: "GroupRollContainerView"

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


class GroupRollRollButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.success, custom_id="roll_btn", label="Roll")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollRollModal(interaction, self.rolls_view))


class GroupRollRollModal(GroupRollModal):
    view: "GroupRollContainerView"
    reason: str
    name_input: BaseLabelTextInput
    modifier_input: BaseLabelTextInput
    force_value_input: ModalCheckboxComponent
    advantage_input: ModalSelectComponent

    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        super().__init__(itr, title=f"Rolling for {view.reason}", view=view)
        display_name = itr.user.display_name.title().strip()
        prev_value = DiceCache.get(itr).get_last_grouproll(view.reason)

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
            default=prev_value,
            placeholder=prev_value,
        )
        self.advantage_input = ModalSelectComponent(
            label="Roll mode",
            placeholder="Normal",
            options=Advantage.options(),
            required=False,
        )
        self.force_value_input = ModalCheckboxComponent(
            label="Force set value",
            default=False,
        )

        self.add_item(self.modifier_input)
        self.add_item(self.force_value_input)
        self.add_item(self.name_input)
        self.add_item(self.advantage_input)

    async def on_submit(self, itr: Interaction):
        name = self.name or ""
        modifier = self.modifier or "0"
        advantage = self.advantage or Advantage.NORMAL

        if self.force_value:
            try:
                value = int(modifier)
            except Exception:
                raise ValueError(f"Could not parse '{modifier}' as an integer when value was force set.")
            group_roll = GroupRollSet(itr, name, value)
            title = f"{itr.user.name} set {self.view.reason} for {group_roll.name}"
            description = f"**{self.view.reason.title()}**: {group_roll.total}"
        else:
            # Only store in the dice cache if the value wasn't forced
            DiceCache.get(itr).store_grouproll(self.view.reason, modifier)

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
    def force_value(self) -> bool:
        return self.force_value_input.value

    @property
    def sound(self) -> SoundType:
        # Specific use case for initiatives
        if self.view.reason == "initiative":
            return SoundType.CREATURE if self.name else SoundType.PLAYER
        return SoundType.ROLL


class GroupRollDeleteButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.danger, custom_id="delete_btn", label="Delete Roll")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollDeleteModal(interaction, self.rolls_view))


class GroupRollDeleteModal(GroupRollModal):
    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        super().__init__(itr, title=f"Remove {view.reason} rolls", view=view)

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


class GroupRollBulkButton(GroupRollButton):
    def __init__(self, view: "GroupRollContainerView"):
        super().__init__(view, style=discord.ButtonStyle.primary, custom_id="bulk_btn", label="Bulk")

    async def callback(self, interaction: Interaction):
        await interaction.response.send_modal(GroupRollBulkModal(interaction, self.rolls_view))


class GroupRollBulkModal(GroupRollModal):
    def __init__(self, itr: Interaction, view: "GroupRollContainerView"):
        super().__init__(itr, title=f"Adding bulk {view.reason} rolls", view=view)

        # Discord only allows for five modals components, so we have to group things together....
        self.modifier_input = BaseLabelTextInput(
            label="Creature's modifier",
            placeholder="0",
            max_length=3,
            required=False,
        )
        self.force_value_input = discord.CheckboxGroupOption(
            label="Force set value",
            value="force_set",
            default=False,
        )
        self.shared_input = discord.CheckboxGroupOption(
            label="Share rolls",
            default=False,
            value="shared",
        )
        self.name_input = BaseLabelTextInput(
            label="Creature's Name",
            max_length=128,
        )
        self.amount_input = BaseLabelTextInput(
            label="Amount of creatures to add",
            placeholder="1 - 25",
            max_length=2,
        )
        self.advantage_input = ModalSelectComponent(
            label="Roll mode",
            placeholder="Normal",
            options=Advantage.options(),
            required=False,
        )

        self.checkbox_group = ModalCheckboxGroupComponent(label="Options", options=[self.force_value_input, self.shared_input])

        self.add_item(self.modifier_input)
        self.add_item(self.checkbox_group)
        self.add_item(self.name_input)
        self.add_item(self.amount_input)
        self.add_item(self.advantage_input)

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
        force_value = self.force_value

        if force_value:
            try:
                value = int(modifier)
            except Exception:
                raise ValueError(f"Could not parse '{modifier}' as an integer when value was force set.")
            rolls = [GroupRollSet(itr, name, value) for _ in range(amount)]
        else:
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
        return any(child == "shared" for child in self.checkbox_group.values)

    @property
    def force_value(self) -> bool:
        return any(child == "force_set" for child in self.checkbox_group.values)


class GroupRollContainerView(ui.LayoutView):
    reason: str
    rolls: dict[str, GroupRoll]
    buttons: list[GroupRollButton]
    buttons_per_row: int

    def __init__(self, reason: str):
        super().__init__(timeout=3600)

        self.reason = reason
        self.rolls = {}
        self.buttons = []
        self.buttons_per_row = 3

        self.buttons.append(GroupRollRollButton(self))
        self.buttons.append(GroupRollBulkButton(self))
        self.buttons.append(GroupRollDeleteButton(self))

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
