import logging

import discord


def log_button_press(itr: discord.Interaction, button: discord.ui.Button[discord.ui.LayoutView], location: str):
    logging.info("%s pressed '%s' in %s", itr.user.name, button.label, location)
