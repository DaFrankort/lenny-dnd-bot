import logging
import discord


def log_button_press(
    itr: discord.Interaction, button: discord.ui.Button, location: str
):
    logging.info(f"{itr.user.name} pressed '{button.label}' in {location}")
