import logging
from typing import Any, TypeVar

from discord import Interaction
from discord.ui import Modal

from commands.command import get_error_embed
from components.items import ModalSelectComponent, BaseLabelTextInput

T = TypeVar("T")


class BaseModal(Modal):
    def __init__(self, itr: Interaction, title: str):
        super().__init__(title=title)
        self.itr = itr

    def log_inputs(self, itr: Interaction):
        """Logs all text input values."""
        input_values = {
            child.text: str(child.input)
            for child in self.children
            if isinstance(child, BaseLabelTextInput) and str(child.input) != ""
        }

        username = itr.user.name
        logging.info("%s submitted modal => %s", username, input_values)

    async def on_error(self, itr: Interaction, error: Exception):
        self.log_inputs(itr)
        embed = get_error_embed(error)
        await itr.response.send_message(embed=embed, ephemeral=True)

    @staticmethod
    def get_str(component: BaseLabelTextInput) -> str | None:
        """Safely parse string from LabeledTextComponent. Returns None if input is empty or only spaces."""
        text = str(component.input).strip()
        return text if text else None

    @staticmethod
    def get_int(component: BaseLabelTextInput) -> int | None:
        """Safely parse integer from LabeledTextComponent. Returns None on failure, defaults to 0 if input is ''"""
        text = str(component.input).strip()
        if text == "":
            return 0
        try:
            return int(text)
        except ValueError:
            return None

    @staticmethod
    def get_choice(component: ModalSelectComponent, result_type: type) -> Any | None:
        """Get the selected choice of a ModalSelectComponent, or None if no choice is selected."""
        if not component.input.values:
            return None
        return result_type(component.input.values[0])

    @staticmethod
    def format_placeholder(text: str, length: int = 100) -> str:
        """Cuts off a string to stay within a modal's 100 character-limit for placeholders."""
        cutoff_str: str = "..."
        length = length - len(cutoff_str)
        return text[:length] + cutoff_str if len(text) > length else text
