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


def check_support(spells: SpellList):
    sorted_spells = sorted(spells.spells, key=lambda s: s.name)
    unsupported = False

    for spell in sorted_spells:
        if "Unsupported" in spell.casting_time:
            logging.warning(f"{spell.name}: {spell.casting_time}")
            unsupported = True
        if "Unsupported" in spell.duration:
            logging.warning(f"{spell.name}: {spell.duration}")
            unsupported = True
        if "Unsupported" in spell.spell_range:
            logging.warning(f"{spell.name}: {spell.spell_range}")
            unsupported = True

        for _, desc in spell.descriptions:
            if "Unsupported" in desc:
                logging.warning(f"{spell.name}: {desc}")
                unsupported = True

    if not unsupported:
        logging.info("No unsupported spells found!")


if __name__ == "__main__":
    os.makedirs("./temp", exist_ok=True)
    bot = Bot()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check-support",
        type=bool,
        default=False,
        action=argparse.BooleanOptionalAction,
    )

    args = parser.parse_args()

    if args.check_support:
        check_support(bot.spells)
    else:
        bot.run_client()
