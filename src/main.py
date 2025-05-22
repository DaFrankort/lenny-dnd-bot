import argparse
import logging
import os
from bot import Bot
from dnd import SpellList

logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG to see all messages, normal is INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Output to console
)


if __name__ == "__main__":
    os.makedirs("./temp", exist_ok=True)
    bot = Bot()
    bot.run_client()
