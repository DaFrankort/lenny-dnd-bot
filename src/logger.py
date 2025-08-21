import logging
import discord


def log_cmd(itr: discord.Interaction):
    """Helper function to log user's command-usage in the terminal"""
    try:
        criteria = [f"[{k}={v}]" for k, v in vars(itr.namespace).items()]
    except Exception:
        criteria = []
    criteria_text = " ".join(criteria)

    logging.info(f"{itr.user.name} => /{itr.command.name} {criteria_text}")


def log_button_press(
    itr: discord.Interaction, button: discord.ui.Button, location: str
):
    logging.info(f"{itr.user.name} pressed '{button.label}' in {location}")
