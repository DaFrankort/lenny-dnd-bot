import logging
from discord import Interaction
from discord.ui import TextInput, Modal
from dice import DiceExpressionCache
from embeds import SuccessEmbed


class SimpleModal(Modal):
    def __init__(self, itr: Interaction, title: str):
        super().__init__(title=title)
        self.itr = itr

    def log_inputs(self, itr: Interaction):
        """Logs all text input values."""
        input_values = {
            child.label: str(child)
            for child in self.children
            if isinstance(child, TextInput) and str(child) != ""
        }

        username = itr.user.name
        logging.info(f"{username} submitted modal => {input_values}")

    async def on_error(self, itr: Interaction, error: Exception):
        self.log_inputs(itr)
        await itr.response.send_message(
            "Something went wrong! Please try again later.", ephemeral=True
        )
        raise error

    def get_str(self, text_input: TextInput) -> str | None:
        """Safely parse string from TextInput. Returns None if input is empty or only spaces."""
        text = str(text_input).strip()
        return text if text else None

    def get_int(self, text_input: TextInput) -> int | None:
        """Safely parse integer from TextInput. Returns None on failure, defaults to 0 if input is ''"""
        text = str(text_input).strip()
        if text == "":
            return 0
        try:
            return int(text)
        except ValueError:
            return None

    def get_choice(
        self, text_input: TextInput, default: any, choices: dict[str, any]
    ) -> any:
        """Used to simulate selection-menu functionality, allowing a user to select a certain option."""
        choice = default
        user_input = str(text_input).lower()

        for key in choices:
            choice_value = choices[key]
            if user_input.startswith(key.lower()):
                choice = choice_value
                break

        return choice


class DiceShortcutAddModal(SimpleModal):
    name: str
    notation = TextInput(
        label="Dice expression",
        placeholder="1d20+6",
    )
    reason = TextInput(
        label="Roll Reason (Optional)",
        placeholder="Attack / Damage / Fire / ...",
        required=False,
    )

    def __init__(self, itr: Interaction, name: str):
        super().__init__(itr, title=f"Adding shortcut: '{name}'")
        self.name = name

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        notation = self.get_str(self.notation)
        reason = self.get_str(self.reason)

        description, success = DiceExpressionCache.store_shortcut(
            itr, self.name, notation, reason
        )
        await itr.response.send_message(
            embed=SuccessEmbed(
                title_success=f"Added roll-shortcut {self.name}!",
                title_fail=f"Failed to add {self.name}...",
                description=description,
                success=success,
            ),
            ephemeral=True,
        )


class DiceShortcutEditModal(SimpleModal):
    name: str
    notation = TextInput(
        label="Dice expression",
    )
    reason = TextInput(
        label="Roll Reason (Optional)",
        required=False,
    )

    def __init__(self, itr: Interaction, name: str, shortcut: object):
        super().__init__(itr, title=f"Editing shortcut: '{name}'")
        self.name = name
        expression = shortcut["expression"]
        reason = shortcut["reason"]

        self.notation.default = expression
        self.notation.placeholder = expression
        self.reason.default = reason
        self.reason.placeholder = reason or "Attack / Damage / Fire / ..."

    async def on_submit(self, itr: Interaction):
        self.log_inputs(itr)

        notation = self.get_str(self.notation)
        reason = self.get_str(self.reason)

        description, success = DiceExpressionCache.store_shortcut(
            itr, self.name, notation, reason
        )
        await itr.response.send_message(
            embed=SuccessEmbed(
                title_success=f"Edited roll-shortcut {self.name}!",
                title_fail=f"Failed to edit {self.name}...",
                description=description,
                success=success,
            ),
            ephemeral=True,
        )
