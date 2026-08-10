import os

from bot import Bot
from logger import setup_logging
from services.config import BotConfig

if __name__ == "__main__":
    # Parse command line arguments, see `python lenny --help`
    config = BotConfig.load()
    setup_logging(config.verbose)

    # Start the bot
    os.makedirs("./temp", exist_ok=True)
    bot = Bot(config)
    bot.run_client()
