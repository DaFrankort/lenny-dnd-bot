import logging
from typing import Any, TypeVar

from discord import Interaction
from discord.ui import Modal

from commands.command import get_error_embed
from components.items import ModalSelectComponent, SimpleLabelTextInput

T = TypeVar("T")


class SimpleModal(Modal):
    def __init__(self, itr: Interaction, title: str):
        super().__init__(title=title)
        self.itr = itr

    def log_inputs(self, itr: Interaction):
        """Logs all text input values."""
        input_values = {
            child.text: str(child.input)
            for child in self.children
            if isinstance(child, SimpleLabelTextInput) and str(child.input) != ""
        }

        username = itr.user.name
        logging.info(f"{username} submitted modal => {input_values}")

    async def on_error(self, itr: Interaction, error: Exception):
        self.log_inputs(itr)
        embed = get_error_embed(error)
        await itr.response.send_message(embed=embed, ephemeral=True)

    def get_str(self, component: SimpleLabelTextInput) -> str | None:
        """Safely parse string from LabeledTextComponent. Returns None if input is empty or only spaces."""
        text = str(component.input).strip()
        return text if text else None

    def get_int(self, component: SimpleLabelTextInput) -> int | None:
        """Safely parse integer from LabeledTextComponent. Returns None on failure, defaults to 0 if input is ''"""
        text = str(component.input).strip()
        if text == "":
            return 0
        try:
            return int(text)
        except ValueError:
            return None

    def get_choice(self, component: ModalSelectComponent, type: type) -> Any | None:
        """Get the selected choice of a ModalSelectComponent, or None if no choice is selected."""
        if not component.input.values:
            return None
        return type(component.input.values[0])

    def format_placeholder(self, text: str, length: int = 100) -> str:
        """Cuts off a string to stay within a modal's 100 character-limit for placeholders."""
        cutoff_str: str = "..."
        length = length - len(cutoff_str)
        return text[:length] + cutoff_str if len(text) > length else text
