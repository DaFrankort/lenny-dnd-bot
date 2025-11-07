import logging
from typing import TypeVar
from discord import Interaction
from discord.ui import TextInput, Modal
from discord.ui.view import BaseView

from command import get_error_embed

T = TypeVar("T")


class SimpleModal(Modal):
    def __init__(self, itr: Interaction, title: str):
        super().__init__(title=title)
        self.itr = itr

    def log_inputs(self, itr: Interaction):
        """Logs all text input values."""
        input_values = {child.label: str(child) for child in self.children if isinstance(child, TextInput) and str(child) != ""}

        username = itr.user.name
        logging.info(f"{username} submitted modal => {input_values}")

    async def on_error(self, itr: Interaction, error: Exception):
        self.log_inputs(itr)
        embed = get_error_embed(error)
        await itr.response.send_message(embed=embed, ephemeral=True)

    def get_str(self, text_input: TextInput[BaseView]) -> str | None:
        """Safely parse string from TextInput. Returns None if input is empty or only spaces."""
        text = str(text_input).strip()
        return text if text else None

    def get_int(self, text_input: TextInput[BaseView]) -> int | None:
        """Safely parse integer from TextInput. Returns None on failure, defaults to 0 if input is ''"""
        text = str(text_input).strip()
        if text == "":
            return 0
        try:
            return int(text)
        except ValueError:
            return None

    def get_choice(self, text_input: TextInput[BaseView], default: T, choices: dict[str, T]) -> T:
        """Used to simulate selection-menu functionality, allowing a user to select a certain option."""
        choice = default
        user_input = str(text_input).lower()

        for key in choices:
            choice_value = choices[key]
            if user_input.startswith(key.lower()):
                choice = choice_value
                break
        return choice

    def format_placeholder(self, text: str) -> str:
        """Cuts off a string to stay within an embed's 100 character-limit for placeholders."""
        return text[:97] + "..." if len(text) > 97 else text
