import logging
import os
from bot import Bot
from discord.utils import _ColourFormatter
import i18n

if __name__ == "__main__":
    # Set-up translations
    i18n.set_locale("./assets/locales/en.json")

    # Set up logging using discord.py's _ColourFormatter
    handler = logging.StreamHandler()
    handler.setFormatter(_ColourFormatter())
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Start the bot
    os.makedirs("./temp", exist_ok=True)
    bot = Bot()
    bot.run_client()
