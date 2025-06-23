import logging
import os
from bot import Bot
from discord.utils import _ColourFormatter
import i18n

if __name__ == "__main__":
    # Set-up translations
    i18n.config.set("locale", "en")
    i18n.config.set("fallback", "en")
    i18n.config.set("file_format", "json")
    i18n.config.set("filename_format", "{locale}.{format}")
    i18n.config.set("skip_locale_root_data", True)
    i18n.load_path.append("assets/translations")  

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
