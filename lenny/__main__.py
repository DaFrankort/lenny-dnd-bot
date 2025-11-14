import argparse
import logging
import os

from discord.utils import (
    _ColourFormatter,  # type: ignore # Discord's private formatter has proven to be quite nice to use
)

from bot import Bot

if __name__ == "__main__":
    # Parse command line arguments, see `python lenny --help`
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
        help="Enable additional logging. Disabled by default.",
    )
    parser.add_argument(
        "--voice",
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Enable voice behavior. Enabled by default.",
    )

    args = parser.parse_args()

    # Set up logging using discord.py's _ColourFormatter
    handler = logging.StreamHandler()
    handler.setFormatter(_ColourFormatter())
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logging.getLogger("discord.player").setLevel(logging.WARNING)

    # Start the bot
    os.makedirs("./temp", exist_ok=True)
    bot = Bot(voice=args.voice)
    bot.run_client()
